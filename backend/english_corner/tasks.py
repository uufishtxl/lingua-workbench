"""
Huey background tasks for English Corner.

Handles:
  - Message processing (Tutor feedback + Character reply + TTS)
  - Initial greeting generation
  - WordNode LLM enrichment
"""
import logging
import traceback
from huey.contrib.djhuey import db_task

logger = logging.getLogger(__name__)


@db_task()
def process_user_message(message_id: int):
    """
    Async pipeline after user sends a message:
    1. Mark user message as PROCESSING
    2. Generate Tutor feedback (polish + explanation)
    3. Generate Character reply
    4. Generate TTS audio for Character reply
    5. Mark everything as SUCCESS
    """
    from .models import PracticeMessage
    from .ai_services import (
        generate_tutor_feedback,
        generate_character_reply,
        generate_tts_audio,
    )

    try:
        user_msg = PracticeMessage.objects.select_related(
            'conversation', 'conversation__scenario'
        ).get(id=message_id)
    except PracticeMessage.DoesNotExist:
        logger.error(f"PracticeMessage {message_id} not found")
        return

    conversation = user_msg.conversation

    try:
        # ========== Phase 1: Mark as processing ==========
        user_msg.status = PracticeMessage.Status.PROCESSING
        user_msg.save(update_fields=['status'])

        # ========== Phase 2: Tutor Feedback ==========
        logger.info(f"[Msg {message_id}] Generating tutor feedback...")
        feedback = generate_tutor_feedback(conversation, user_msg.user_content)
        user_msg.tutor_polished_text = feedback.get('polished_text', '')
        user_msg.tutor_explanation_cn = feedback.get('explanation_cn', '')
        user_msg.save(update_fields=['tutor_polished_text', 'tutor_explanation_cn'])

        # ========== Phase 3: Character Reply ==========
        logger.info(f"[Msg {message_id}] Generating character reply...")
        character_text = generate_character_reply(conversation, user_msg.user_content)

        # Create the assistant message
        ai_msg = PracticeMessage.objects.create(
            conversation=conversation,
            role=PracticeMessage.Role.ASSISTANT,
            status=PracticeMessage.Status.PROCESSING,
            character_content=character_text,
        )

        # ========== Phase 4: TTS ==========
        logger.info(f"[Msg {message_id}] Generating TTS audio...")
        audio_url = generate_tts_audio(character_text, conversation.id, ai_msg.id)
        ai_msg.audio_url = audio_url

        # ========== Phase 5: Mark SUCCESS ==========
        ai_msg.status = PracticeMessage.Status.SUCCESS
        ai_msg.is_processed = True
        ai_msg.save(update_fields=['audio_url', 'status', 'is_processed'])

        user_msg.status = PracticeMessage.Status.SUCCESS
        user_msg.is_processed = True
        user_msg.save(update_fields=['status', 'is_processed'])

        logger.info(f"[Msg {message_id}] Processing complete ✅")

    except Exception as e:
        logger.exception(f"[Msg {message_id}] Processing failed: {e}")
        user_msg.status = PracticeMessage.Status.FAILED
        user_msg.save(update_fields=['status'])


@db_task()
def process_initial_greeting(conversation_id: int):
    """
    Generate the first AI greeting message when a conversation starts.
    1. Generate Character greeting
    2. Generate TTS
    3. Create PracticeMessage with SUCCESS status
    """
    from .models import Conversation, PracticeMessage
    from .ai_services import generate_character_reply, generate_tts_audio

    try:
        conversation = Conversation.objects.select_related('scenario').get(
            id=conversation_id
        )
    except Conversation.DoesNotExist:
        logger.error(f"Conversation {conversation_id} not found")
        return

    try:
        # Generate greeting
        logger.info(f"[Conv {conversation_id}] Generating initial greeting...")
        greeting_text = generate_character_reply(conversation, "")

        # Create assistant message
        ai_msg = PracticeMessage.objects.create(
            conversation=conversation,
            role=PracticeMessage.Role.ASSISTANT,
            status=PracticeMessage.Status.PROCESSING,
            character_content=greeting_text,
        )

        # Generate TTS
        logger.info(f"[Conv {conversation_id}] Generating TTS for greeting...")
        audio_url = generate_tts_audio(greeting_text, conversation.id, ai_msg.id)

        # Finalize
        ai_msg.audio_url = audio_url
        ai_msg.status = PracticeMessage.Status.SUCCESS
        ai_msg.is_processed = True
        ai_msg.save(update_fields=['audio_url', 'status', 'is_processed'])

        logger.info(f"[Conv {conversation_id}] Greeting ready ✅")

    except Exception as e:
        logger.exception(f"[Conv {conversation_id}] Greeting generation failed: {e}")
        # Create a failed message so frontend knows something went wrong
        PracticeMessage.objects.create(
            conversation=conversation,
            role=PracticeMessage.Role.ASSISTANT,
            status=PracticeMessage.Status.FAILED,
            character_content="Sorry, I couldn't start the conversation. Please try again.",
        )


@db_task()
def enrich_word_node(word_node_id: int):
    """
    Async LLM enrichment for a WordNode:
    1. Call LLM to generate explanation (中文释义) + example sentence
    2. Update the WordNode fields
    3. Set status to SUCCESS
    """
    from .models import WordNode
    from .ai_services import generate_word_enrichment

    try:
        node = WordNode.objects.get(id=word_node_id)
    except WordNode.DoesNotExist:
        logger.error(f"WordNode {word_node_id} not found")
        return

    try:
        logger.info(f"[WordNode {word_node_id}] Enriching '{node.label}'...")

        # Get context from phrase_log if available
        context = ""
        if node.phrase_log:
            context = node.phrase_log.original_context or ""

        result = generate_word_enrichment(node.label, context)

        node.explanation = result.get('explanation', '')
        node.example = result.get('example', '')
        node.status = WordNode.Status.SUCCESS
        node.save(update_fields=['explanation', 'example', 'status'])

        # Also sync back to PhraseLog if linked
        if node.phrase_log:
            node.phrase_log.chinese_meaning = node.explanation
            node.phrase_log.example_sentence = node.example
            node.phrase_log.save(update_fields=['chinese_meaning', 'example_sentence'])

        logger.info(f"[WordNode {word_node_id}] Enrichment complete ✅")

    except Exception as e:
        logger.exception(f"[WordNode {word_node_id}] Enrichment failed: {e}")
        node.status = WordNode.Status.FAILED
        node.save(update_fields=['status'])
