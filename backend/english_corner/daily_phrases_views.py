"""
Views for Daily Phrases feature.

Endpoints:
  - GET  /api/v1/daily-phrases/init/          → Initialize or resume daily session
  - POST /api/v1/daily-phrases/verify/        → Verify sentence & update SRS
  - GET  /api/v1/daily-phrases/refresh-bonus/ → Refresh bonus word pool
"""
import logging
from datetime import timedelta

from django.db.models import F
from django.db.models.functions import Least
from django.utils import timezone
from rest_framework import views, status, serializers
from rest_framework.response import Response

from .models import WordNode, DailyPracticeLog
from .daily_phrases_utils import get_random_bonus_words
from .serializers import DailyPhrasesVerifySerializer
from .ai_services import generate_batch_scenarios, verify_user_sentence

logger = logging.getLogger(__name__)

# ================================================================
# Constants
# ================================================================
DAILY_PRACTICE_LIMIT = 3
BOX_LEVEL_CAP = 5


# ================================================================
# GET /api/v1/daily-phrases/init/
# ================================================================

class DailyPhrasesInitView(views.APIView):
    """
    Initialize or resume today's daily practice session.
    - Creates DailyPracticeLog if none exists for today.
    - Picks 3 due WordNodes (fallback: box_level=1).
    - Batch-generates scenarios for words missing them.
    - Returns session data or "completed" state.
    """

    def get(self, request):
        user = request.user
        today = timezone.now().date()
        now = timezone.now()

        # 1. Get or create today's log
        log, created = DailyPracticeLog.objects.get_or_create(
            user=user,
            date=today,
        )

        # 2. If already completed → return Rocket/done payload
        if log.is_completed:
            return Response({
                "is_completed": True,
                "words_practiced": log.words_practiced,
                "completed_at": log.updated_at,
                "summary": {
                    "focus_minutes": log.focus_minutes,
                    # Placeholder: 100% accuracy as this is a self-driven practice. 
                    # We emphasize accumulation and real-world usage over scoring.
                    "daily_streak_percent": 100,
                },
            })

        # 3. If no words selected yet → pick them
        if not log.word_ids:
            # Primary: words due for review
            due_words = list(
                WordNode.objects.filter(
                    user=user,
                    next_review_at__lte=now,
                ).order_by('?')[:DAILY_PRACTICE_LIMIT]
                .values_list('id', flat=True)
            )

            # Fallback: if not enough due words, fill from box_level=1
            if len(due_words) < DAILY_PRACTICE_LIMIT:
                fallback = list(
                    WordNode.objects.filter(user=user, box_level=1)
                    .exclude(id__in=due_words)
                    .order_by('?')[: DAILY_PRACTICE_LIMIT - len(due_words)]
                    .values_list('id', flat=True)
                )
                due_words.extend(fallback)

            if not due_words:
                # If there are no words to practice at all, mark as natively complete
                log.is_completed = True
                log.save(update_fields=['is_completed'])
                return Response({
                    "is_completed": True,
                    "words_practiced": log.words_practiced,
                    "completed_at": log.updated_at,
                    "summary": {
                        "focus_minutes": log.focus_minutes,
                        # Placeholder: 100% accuracy as this is a self-driven practice. 
                        # We emphasize accumulation and real-world usage over scoring.
                        "daily_streak_percent": 100,
                    },
                })

            log.word_ids = due_words
            log.save(update_fields=['word_ids'])

        # 4. Fetch full WordNode data
        word_nodes = WordNode.objects.filter(id__in=log.word_ids)
        word_map = {w.id: w for w in word_nodes}

        # 5. Batch scenario generation for words missing scenarios
        words_needing_scenarios = [
            {"id": w.id, "label": w.label}
            for w in word_nodes if not w.scenarios
        ]

        if words_needing_scenarios:
            try:
                scenarios_result = generate_batch_scenarios(words_needing_scenarios)
                # Bulk update WordNode.scenarios
                for word_data in words_needing_scenarios:
                    word_obj = word_map[word_data['id']]
                    generated = scenarios_result.get(word_data['label'], [])
                    if generated:
                        word_obj.scenarios = generated
                        word_obj.save(update_fields=['scenarios'])
            except Exception as e:
                logger.exception(f"Batch scenario generation failed: {e}")

        # 6. Fetch unique bonus words pool for each target word
        num_targets = len(log.word_ids)
        bonus_pool = get_random_bonus_words(
            user, 
            exclude_ids=log.word_ids, 
            count=num_targets * 3
        )

        # 7. Build response — Distribute 3 unique bonus words to each target
        session_words = []
        for i, wid in enumerate(log.word_ids): # [3, 19, 39]
            w = word_map.get(wid) # {3: "some", 19: "any", 39: "very"}
            if not w:
                continue
            
            # Slice the pool: 3 words per target
            start = i * 3 # 0, 3, 6
            word_bonus = bonus_pool[start : start + 3]

            session_words.append({
                "id": w.id,
                "word": w.label,
                "explanation": w.explanation,
                "scenarios": w.scenarios or [],
                "bonus_words": word_bonus,
            })

        return Response({
            "is_completed": False,
            "words_practiced": log.words_practiced,
            "session_words": session_words,
        })


# ================================================================
# POST /api/v1/daily-phrases/verify/
# ================================================================

class DailyPhrasesVerifyView(views.APIView):
    """
    Verify user's sentence via LLM, update SRS, advance daily progress.
    """

    def post(self, request):
        serializer = DailyPhrasesVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        word_id = data['word_id']
        user_sentence = data['user_sentence']
        active_bonus_words = data.get('active_bonus_words', [])

        user = request.user

        # 1. Validate target word belongs to user
        try:
            target_word = WordNode.objects.get(id=word_id, user=user)
        except WordNode.DoesNotExist:
            return Response(
                {"error": "Word not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # 2. Call LLM verification
        verification = verify_user_sentence(
            target_word=target_word.label,
            user_sentence=user_sentence,
            bonus_words=active_bonus_words,
        )

        # 3. SRS update — Target word
        now = timezone.now()
        if verification['is_pass']:
            target_word.box_level = min(target_word.box_level + 1, BOX_LEVEL_CAP)
        else:
            target_word.box_level = 1

        target_word.next_review_at = now + timedelta(days=2 ** target_word.box_level)
        target_word.save(update_fields=['box_level', 'next_review_at'])

        # 4. SRS update — Bonus words (mastered ones only)
        mastered_ids = verification['mastered_word_ids']
        if mastered_ids:
            # Security: only update words belonging to this user
            WordNode.objects.filter(
                id__in=mastered_ids,
                user=user,
            ).update(
                box_level=Least(F('box_level') + 1, BOX_LEVEL_CAP),
                next_review_at=now + timedelta(days=4),  # conservative boost
            )

        # 5. Update DailyPracticeLog
        today = now.date()
        try:
            log = DailyPracticeLog.objects.get(user=user, date=today)
            target_limit = len(log.word_ids) if log.word_ids else DAILY_PRACTICE_LIMIT
            
            # Update DailyPracticeLog progress
            log.words_practiced += 1
            if log.words_practiced >= target_limit:
                log.is_completed = True
            log.save(update_fields=['words_practiced', 'is_completed', 'updated_at'])

            # 6. Response
            return Response({
                "session_progress": {
                    "words_practiced": log.words_practiced,
                    "target_limit": target_limit,
                    "is_completed": log.is_completed,
                },
                "verification": {
                    "is_pass": verification['is_pass'],
                    "polished_text": verification['polished_text'],
                    "native_version": verification['native_version'],
                    "community_version": verification['community_version'],
                    "feedback": verification['feedback'],
                    "mastered_word_ids": mastered_ids,
                    "alternatives": verification['alternatives'],
                },
            })
        except DailyPracticeLog.DoesNotExist:
            logger.warning(f"DailyPracticeLog not found for user {user.id} on {today}")
            return Response({"error": "Log not found"}, status=status.HTTP_404_NOT_FOUND)


# ================================================================
# GET /api/v1/daily-phrases/refresh-bonus/
# ================================================================

class RefreshBonusView(views.APIView):
    """
    Refresh the bonus word pool, excluding specified IDs.
    """

    def get(self, request):
        user = request.user
        exclude_str = request.query_params.get('exclude_ids', '')
        exclude_ids = []
        if exclude_str:
            try:
                exclude_ids = [int(x) for x in exclude_str.split(',') if x.strip()]
            except ValueError:
                return Response(
                    {"error": "exclude_ids must be comma-separated integers."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        bonus_words = get_random_bonus_words(user, exclude_ids=exclude_ids)
        return Response({"bonus_words": bonus_words})
