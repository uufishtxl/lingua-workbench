from rest_framework import viewsets, views, status, response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from .models import (
    Scenario, Conversation, PracticeMessage,
    PracticeFlashcard, WordNode, WordOccurrence, WordLink,
)
from .serializers import (
    ScenarioSerializer, ConversationSerializer, ConversationDetailSerializer,
    PracticeMessageSerializer, PracticeFlashcardSerializer, WordNodeSerializer,
)
from .ai_services import generate_scenario_prompt, generate_flashcard
from .tasks import process_user_message, process_initial_greeting, enrich_word_node
from phrase_log.models import PhraseLog
import re

def extract_best_sentence(sources, target_text):
    """
    Helper to find the best sentence context from multiple text sources.
    sources: list of strings
    target_text: the word/phrase to find
    """
    best_sentence = ""
    best_score = -1
    target_phrase = target_text.lower()
    
    # Pre-calculate core words for fuzzy matching
    target_words = set(re.findall(r'\w+', target_phrase))
    stop_words = {'a', 'an', 'the', 'to', 'in', 'on', 'at', 'of', 'for', 'with'}
    target_core = target_words - stop_words

    for full_text in sources:
        if not full_text: continue
        # Split and keep the punctuation to avoid look-behind issues with variable width
        parts = re.split(r'([.!?。！？][\"\'”’]*)(?:\s+|$)', full_text.strip())
        sentences = []
        for i in range(0, len(parts) - 1, 2):
            if parts[i] or parts[i+1]:
                sentences.append((parts[i] or "") + (parts[i+1] or ""))
        if len(parts) % 2 != 0 and parts[-1]:
            sentences.append(parts[-1])
        
        for sentence in sentences:
            sentence_lower = sentence.lower()
            # 1. Exact substring match (highest priority)
            if target_phrase in sentence_lower:
                return sentence.strip()
                
            # 2. Fuzzy overlap match (fallback)
            if target_core:
                sentence_words = set(re.findall(r'\w+', sentence_lower))
                overlap = len(target_core & sentence_words)
                if overlap > best_score and overlap > 0:
                    best_score = overlap
                    best_sentence = sentence.strip()
                    
    return best_sentence


# ================================================================
# Scenario CRUD
# ================================================================

class ScenarioViewSet(viewsets.ModelViewSet):
    """
    GET  /api/scenarios/     — list (presets + user's custom)
    POST /api/scenarios/     — create custom scenario (auto-generates system_prompt)
    """
    serializer_class = ScenarioSerializer
    pagination_class = None

    def get_queryset(self):
        from django.db.models import Count, Q
        return Scenario.objects.filter(
            Q(is_preset=True) | Q(user=self.request.user)
        ).annotate(
            dialogue_rounds=Count(
                'conversation__messages', 
                filter=Q(conversation__messages__role='user')
            )
        ).order_by('-is_preset', '-created_at')

    def perform_create(self, serializer):
        # Save with user
        scenario = serializer.save(user=self.request.user)

        # Auto-generate system_prompt if not provided
        if not scenario.system_prompt:
            try:
                prompt = generate_scenario_prompt(
                    scenario.title, scenario.description
                )
                scenario.system_prompt = prompt
                scenario.save(update_fields=['system_prompt'])
            except Exception:
                # Fallback: use a basic prompt
                scenario.system_prompt = (
                    f"You are a character in the scenario: {scenario.title}. "
                    f"Setting: {scenario.description}. "
                    f"Stay in character and have a natural English conversation."
                )
                scenario.save(update_fields=['system_prompt'])


# ================================================================
# Conversation Management
# ================================================================

class ConversationViewSet(viewsets.ModelViewSet):
    """
    POST /api/conversations/        — create + dispatch greeting
    GET  /api/conversations/{id}/   — detail with recent messages
    """
    serializer_class = ConversationSerializer
    pagination_class = None

    def get_queryset(self):
        return Conversation.objects.filter(
            user=self.request.user
        ).select_related('scenario').order_by('-created_at')

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ConversationDetailSerializer
        return ConversationSerializer

    def create(self, request, *args, **kwargs):
        scenario_id = request.data.get('scenario')
        if scenario_id:
            # Check for an active conversation for this user and scenario
            existing_conv = Conversation.objects.filter(
                user=request.user, 
                scenario_id=scenario_id, 
                is_active=True
            ).order_by('-created_at').first()
            
            if existing_conv:
                # Return the existing conversation without creating a new one
                serializer = self.get_serializer(existing_conv)
                return response.Response(serializer.data, status=status.HTTP_200_OK)

        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        conversation = serializer.save(user=self.request.user)
        # Dispatch async greeting generation
        process_initial_greeting(conversation.id)


# ================================================================
# Message Interaction (Async 202 Pattern)
# ================================================================

class MessageListCreateView(views.APIView):
    """
    POST /api/conversations/{conv_id}/messages/
        → save user message, dispatch async processing, return 202
    GET  /api/conversations/{conv_id}/messages/
        → return recent messages for the conversation
    """
    def get(self, request, conv_id):
        conversation = get_object_or_404(
            Conversation, id=conv_id, user=request.user
        )
        try:
            limit = int(request.query_params.get('limit', 10))
            offset = int(request.query_params.get('offset', 0))
        except (ValueError, TypeError):
            limit, offset = 10, 0
            
        messages_qs = conversation.messages.order_by('-created_at')[offset : offset + limit]
        messages_list = list(reversed(messages_qs))
        serializer = PracticeMessageSerializer(messages_list, many=True)
        
        has_more = conversation.messages.count() > (offset + limit)
        return response.Response({
            "results": serializer.data,
            "has_more": has_more
        })

    def post(self, request, conv_id):
        conversation = get_object_or_404(
            Conversation, id=conv_id, user=request.user
        )
        user_content = request.data.get('content', '').strip()
        if not user_content:
            return response.Response(
                {"error": "Content is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Create user message with PENDING status
        user_msg = PracticeMessage.objects.create(
            conversation=conversation,
            role=PracticeMessage.Role.USER,
            user_content=user_content,
            status=PracticeMessage.Status.PENDING,
        )

        # Dispatch async processing
        process_user_message(user_msg.id)

        # Return 202 Accepted with message_id
        return response.Response(
            {"message_id": user_msg.id},
            status=status.HTTP_202_ACCEPTED,
        )


class MessageDetailView(views.APIView):
    """
    GET /api/conversations/{conv_id}/messages/{msg_id}/
        → return message status + data (for polling)
    """
    def get(self, request, conv_id, msg_id):
        message = get_object_or_404(
            PracticeMessage,
            id=msg_id,
            conversation_id=conv_id,
            conversation__user=request.user,
        )
        serializer = PracticeMessageSerializer(message)
        return response.Response(serializer.data)


# ================================================================
# Flashcard Generation (Highlight → Card)
# ================================================================

class FlashcardGenerateView(views.APIView):
    """
    POST /api/flashcards/generate/
    Payload: {"message_id": int, "text": "highlighted phrase"}
    Synchronously generates a flashcard via LLM.
    """
    def post(self, request):
        text = request.data.get('text', '').strip()
        message_id = request.data.get('message_id')

        if not text:
            return response.Response(
                {"error": "Text is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get context from the source message
        context = ""
        source_message = None
        if message_id:
            source_message = PracticeMessage.objects.filter(
                id=message_id,
                conversation__user=request.user,
            ).first()
            if source_message:
                context = (
                    source_message.character_content
                    or source_message.user_content
                )

        # Generate flashcard via LLM (synchronous — it's fast enough)
        card_data = generate_flashcard(text, context)

        # Save to DB
        flashcard = PracticeFlashcard.objects.create(
            user=request.user,
            message=source_message,
            target_phrase=card_data.get('target_phrase', text),
            prompt_question=card_data.get('prompt_question', ''),
            answer=card_data.get('answer', text),
            example_context=card_data.get('example_context', context),
        )

        serializer = PracticeFlashcardSerializer(flashcard)
        return response.Response(serializer.data, status=status.HTTP_201_CREATED)


# ================================================================
# Review Today
# ================================================================

class ReviewTodayView(views.APIView):
    """
    GET /api/review/today/
    Returns flashcards due for review (next_review_at <= now).
    """
    def get(self, request):
        now = timezone.now()
        cards = PracticeFlashcard.objects.filter(
            user=request.user,
            next_review_at__lte=now,
        ).order_by('next_review_at')

        serializer = PracticeFlashcardSerializer(cards, many=True)
        return response.Response(serializer.data)


class ReviewSubmitView(views.APIView):
    """
    POST /api/flashcards/{id}/review/
    Payload: {"success": boolean}
    Updates SRS counters (box_level, next_review_at).
    """
    def post(self, request, pk):
        flashcard = get_object_or_404(
            PracticeFlashcard, id=pk, user=request.user
        )
        success = request.data.get('success', False)
        
        # Leitner System: 
        #   Success: box_level++, next_review_at += intervals[box_level]
        #   Failure: box_level = 1, next_review_at += 1 day
        intervals = {
            1: 1,      # 1 day
            2: 3,      # 3 days
            3: 7,      # 1 week
            4: 14,     # 2 weeks
            5: 30,     # 1 month
        }
        
        if success:
            if flashcard.box_level < 5:
                flashcard.box_level += 1
        else:
            flashcard.box_level = 1
            
        days = intervals.get(flashcard.box_level, 1)
        flashcard.next_review_at = timezone.now() + timezone.timedelta(days=days)
        flashcard.save()

        # Update associated WordNode mastery if exists
        # Find the WordNode associated with this phrase text
        word_node = WordNode.objects.filter(
            user=request.user, 
            label__iexact=flashcard.target_phrase
        ).first()
        if word_node:
            # Simple mastery logic: box_level * 20
            word_node.mastery = flashcard.box_level * 20
            word_node.box_level = flashcard.box_level
            word_node.save()

        return response.Response({
            "status": "SAVED",
            "box_level": flashcard.box_level,
            "next_review_at": flashcard.next_review_at
        })


# ================================================================
# Extract Vocab (Highlight → WordNode + async enrichment)
# ================================================================

class ExtractVocabView(views.APIView):
    """
    POST /api/extract/
    Creates a WordNode and dispatches LLM enrichment via Huey.
    Returns 201 immediately; WordNode.status tracks enrichment progress.
    """
    @transaction.atomic
    def post(self, request):
        user = request.user
        text = request.data.get('text', '').strip()
        scenario_id = request.data.get('scenario_id')
        message_id = request.data.get('message_id')
        context = request.data.get('context_sentence', '')

        if not text:
            return response.Response(
                {"error": "Text required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 1. Sync / Create PhraseLog
        phrase_item, created = PhraseLog.objects.get_or_create(
            user=user,
            expression_text=text,
            defaults={
                'original_context': context,
                'chinese_meaning': '(AI 生成中...)',
                'example_sentence': context or '...',
            }
        )

        # 2. Create WordNode (PENDING status)
        node, node_created = WordNode.objects.get_or_create(
            user=user,
            phrase_log=phrase_item,
            defaults={
                'label': text,
                'node_type': 'phrase' if ' ' in text else 'keyword',
                'status': WordNode.Status.PENDING,
            }
        )

        # 3. Create link to scenario or message if provided
        if message_id:
            try:
                from django.contrib.contenttypes.models import ContentType
                msg_obj = PracticeMessage.objects.get(id=message_id)
                ctype = ContentType.objects.get_for_model(PracticeMessage)
                # sources to look into
                sources = [
                    msg_obj.character_content,
                    msg_obj.user_content,
                    msg_obj.tutor_polished_text
                ]
                exact_sentence = extract_best_sentence(sources, text) or text.strip()

                WordOccurrence.objects.get_or_create(
                    user=user,
                    word=node,
                    content_type=ctype,
                    object_id=str(message_id),
                    defaults={'exact_sentence': exact_sentence}
                )
            except PracticeMessage.DoesNotExist:
                pass
        elif scenario_id:
            try:
                from django.contrib.contenttypes.models import ContentType
                scenario_obj = Scenario.objects.get(id=scenario_id)
                ctype = ContentType.objects.get_for_model(Scenario)
                WordOccurrence.objects.get_or_create(
                    user=user,
                    word=node,
                    content_type=ctype,
                    object_id=str(scenario_id),
                    defaults={'exact_sentence': scenario_obj.description or scenario_obj.title or ""}
                )
            except Scenario.DoesNotExist:
                pass

        # 4. Dispatch async enrichment (only if newly created)
        if node_created:
            enrich_word_node(node.id)

        return response.Response(
            WordNodeSerializer(node).data,
            status=status.HTTP_201_CREATED,
        )


# ================================================================
# Knowledge Graph
# ================================================================

class KnowledgeGraphView(views.APIView):
    """
    GET /api/relationship-graph/
    Returns nodes + links for ECharts visualization.
    """
    def get(self, request):
        user = request.user
        scenario_id = request.query_params.get('scenario_id')

        nodes = WordNode.objects.filter(user=user).order_by('created_at')
        from django.contrib.contenttypes.models import ContentType
        msg_ctype = ContentType.objects.get_for_model(PracticeMessage)
        occurrences = WordOccurrence.objects.filter(user=user, content_type=msg_ctype).order_by('created_at')

        if scenario_id:
            # Only show nodes and links for messages in this specific scenario
            message_ids = PracticeMessage.objects.filter(
                conversation__scenario_id=scenario_id
            ).values_list('id', flat=True)
            
            # Filter occurrences for these messages
            message_ids_str = [str(mid) for mid in message_ids]
            occurrences = occurrences.filter(object_id__in=message_ids_str)
            
            # Filter nodes to only those connected via the filtered occurrences
            connected_node_ids = occurrences.values_list('word_id', flat=True).distinct()
            nodes = nodes.filter(id__in=connected_node_ids)

        # Group words by message
        from collections import defaultdict
        message_words = defaultdict(list)
        for occ in occurrences:
            message_words[occ.object_id].append(occ.word_id)

        word_links = []
        node_messages = defaultdict(list)
        
        for message_id, words in message_words.items():
            # Create a chain of words in the same message based on creation order
            for i in range(len(words) - 1):
                word_links.append({
                    "source": words[i],
                    "target": words[i+1],
                    "relation": "Same Message"
                })
            # Also populate node_messages
            for w in words:
                node_messages[int(w)].append(int(message_id))

        nodes_data = WordNodeSerializer(nodes, many=True).data
        for node in nodes_data:
            node['message_ids'] = node_messages.get(node['id'], [])

        return response.Response({
            "nodes": nodes_data,
            "links": word_links,
        })
