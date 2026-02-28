"""
LangGraph Tools for Script Management

Database manipulation tools that the ScriptEditor agent can invoke.
Each tool is decorated with @tool for LangChain/LangGraph compatibility.
"""
from langchain_core.tools import tool
from typing import Optional


@tool
def get_surrounding_lines(line_id: int, radius: int = 3) -> str:
    """Fetch surrounding script lines for context.
    
    Returns ±N lines around the reference line (same chunk, ordered by `order`).
    Use this BEFORE insert_script_line to understand the context and infer
    speaker, line_type, and content style.
    
    Args:
        line_id: The ID of the reference ScriptLine.
        radius: Number of lines above and below to include (default 3).
    """
    from scripts.models import ScriptLine
    
    try:
        ref_line = ScriptLine.objects.get(id=line_id)
    except ScriptLine.DoesNotExist:
        return f"Error: ScriptLine with id={line_id} not found."
    
    # Get surrounding lines in the same chunk, ordered by `order`
    siblings = ScriptLine.objects.filter(
        chunk=ref_line.chunk,
    ).order_by('order')
    
    # Find the position of the reference line
    siblings_list = list(siblings.values_list('id', flat=True))
    try:
        ref_idx = siblings_list.index(ref_line.id)
    except ValueError:
        return f"Error: Could not locate line {line_id} among its siblings."
    
    start = max(0, ref_idx - radius)
    end = min(len(siblings_list), ref_idx + radius + 1)
    
    # Fetch the surrounding slice
    surrounding_ids = siblings_list[start:end]
    surrounding = ScriptLine.objects.filter(id__in=surrounding_ids).order_by('order')
    
    lines = []
    for line in surrounding:
        marker = " <<<" if line.id == ref_line.id else ""
        speaker = line.speaker or "(no speaker)"
        lines.append(
            f"[ID:{line.id} | order:{line.order} | type:{line.line_type}] "
            f"{speaker}: {line.text}"
            f"{' | zh: ' + line.text_zh if line.text_zh else ''}"
            f"{marker}"
        )
    
    # Find prev/next chunks (same source_audio, adjacent chunk_index)
    from audio_slicer.models import AudioChunk
    current_chunk = ref_line.chunk
    prev_chunk = (
        AudioChunk.objects.filter(
            source_audio=current_chunk.source_audio,
            chunk_index=current_chunk.chunk_index - 1,
        ).first()
    )
    next_chunk = (
        AudioChunk.objects.filter(
            source_audio=current_chunk.source_audio,
            chunk_index=current_chunk.chunk_index + 1,
        ).first()
    )
    prev_info = f"prev_chunk_id={prev_chunk.id}" if prev_chunk else "prev_chunk=None (first chunk)"
    next_info = f"next_chunk_id={next_chunk.id}" if next_chunk else "next_chunk=None (last chunk)"

    header = (
        f"Context around line #{line_id} "
        f"(chunk_id={ref_line.chunk_id}, {prev_info}, {next_info}, showing {len(lines)} lines):\n"
    )
    return header + "\n".join(lines)


@tool
def insert_script_line(
    chunk_id: int,
    reference_line_id: int,
    position: str,
    speaker: str,
    text: str,
    text_zh: str = "",
    line_type: str = "dialogue",
    action_note: str = "",
) -> str:
    """Insert a new script line before or after a reference line.
    
    IMPORTANT: Always call get_surrounding_lines first to understand context.
    
    Args:
        chunk_id: The chunk this line belongs to (get from surrounding context).
        reference_line_id: The ID of the existing line to insert relative to.
        position: 'before' or 'after' the reference line.
        speaker: Speaker name (e.g. 'Ross', 'Rachel'). Required for dialogue.
        text: The clean English text of the line.
        text_zh: Chinese translation (generate one if user didn't provide).
        line_type: 'dialogue', 'action', or 'scene' (default: 'dialogue').
        action_note: Optional action/stage direction in parentheses.
    """
    from scripts.models import ScriptLine
    
    if position not in ('before', 'after'):
        return "Error: position must be 'before' or 'after'."
    
    try:
        ref_line = ScriptLine.objects.get(id=reference_line_id)
    except ScriptLine.DoesNotExist:
        return f"Error: ScriptLine with id={reference_line_id} not found."
    
    # Get ordered siblings in the same chunk
    siblings = list(
        ScriptLine.objects.filter(chunk=ref_line.chunk)
        .order_by('order')
        .values_list('id', 'order')
    )
    
    ref_idx = None
    for i, (sid, sorder) in enumerate(siblings):
        if sid == ref_line.id:
            ref_idx = i
            break
    
    if ref_idx is None:
        return f"Error: Could not locate reference line {reference_line_id} in its chunk."
    
    # Calculate new_order using the float average formula
    ref_order = siblings[ref_idx][1]
    
    if position == 'before':
        if ref_idx == 0:
            new_order = ref_order - 1.0
        else:
            prev_order = siblings[ref_idx - 1][1]
            new_order = (prev_order + ref_order) / 2.0
    else:  # after
        if ref_idx == len(siblings) - 1:
            new_order = ref_order + 1.0
        else:
            next_order = siblings[ref_idx + 1][1]
            new_order = (ref_order + next_order) / 2.0
    
    # Build raw_text in canonical format
    raw_text = f"{speaker}: {text}" if speaker else text
    
    # Create the new ScriptLine
    new_line = ScriptLine.objects.create(
        chunk_id=chunk_id,
        index=-1,  # -1 marks manually inserted lines
        order=new_order,
        line_type=line_type,
        speaker=speaker if line_type == 'dialogue' else None,
        text=text,
        text_zh=text_zh,
        action_note=action_note,
        raw_text=raw_text,
    )
    
    return (
        f"Successfully inserted new line!\n"
        f"  ID: {new_line.id}\n"
        f"  Order: {new_order}\n"
        f"  Position: {position} line #{reference_line_id}\n"
        f"  Speaker: {speaker}\n"
        f"  Text: {text}\n"
        f"  Text (zh): {text_zh}"
    )


@tool
def edit_script_line(
    line_id: int,
    speaker: Optional[str] = None,
    text: Optional[str] = None,
    text_zh: Optional[str] = None,
    line_type: Optional[str] = None,
    action_note: Optional[str] = None,
) -> str:
    """Edit an existing script line. Only provided fields will be updated.
    
    Use this to fix errors in the script: wrong speaker, typos, missing translations, etc.
    
    Args:
        line_id: The ID of the ScriptLine to edit.
        speaker: New speaker name (optional).
        text: New English text (optional).
        text_zh: New Chinese translation (optional).
        line_type: New line type: 'dialogue', 'action', or 'scene' (optional).
        action_note: New action note (optional).
    """
    from scripts.models import ScriptLine
    
    try:
        line = ScriptLine.objects.get(id=line_id)
    except ScriptLine.DoesNotExist:
        return f"Error: ScriptLine with id={line_id} not found."
    
    # Track changes for the diff
    changes = []
    
    if speaker is not None and speaker != line.speaker:
        changes.append(f"  speaker: '{line.speaker}' → '{speaker}'")
        line.speaker = speaker
    
    if text is not None and text != line.text:
        changes.append(f"  text: '{line.text[:50]}...' → '{text[:50]}...'")
        line.text = text
    
    if text_zh is not None and text_zh != line.text_zh:
        old_zh = line.text_zh or "(empty)"
        changes.append(f"  text_zh: '{old_zh[:50]}' → '{text_zh[:50]}'")
        line.text_zh = text_zh
    
    if line_type is not None and line_type != line.line_type:
        changes.append(f"  line_type: '{line.line_type}' → '{line_type}'")
        line.line_type = line_type
    
    if action_note is not None and action_note != line.action_note:
        old_note = line.action_note or "(empty)"
        changes.append(f"  action_note: '{old_note[:50]}' → '{action_note[:50]}'")
        line.action_note = action_note
    
    if not changes:
        return f"No changes detected for line #{line_id}. Nothing was updated."
    
    # Auto-sync raw_text if speaker or text changed
    if speaker is not None or text is not None:
        current_speaker = line.speaker or ""
        current_text = line.text
        line.raw_text = f"{current_speaker}: {current_text}" if current_speaker else current_text
        changes.append(f"  raw_text: auto-synced → '{line.raw_text[:60]}...'")
    
    line.save()
    
    return (
        f"Successfully updated line #{line_id}:\n"
        + "\n".join(changes)
    )


@tool
def delete_script_line(line_id: int) -> str:
    """Delete an existing script line.
    
    Use this to remove lines that are hallucinatory, duplicates, or completely irrelevant.
    
    Args:
        line_id: The ID of the ScriptLine to delete.
    """
    from scripts.models import ScriptLine
    
    try:
        line = ScriptLine.objects.get(id=line_id)
    except ScriptLine.DoesNotExist:
        return f"Error: ScriptLine with id={line_id} not found."
    
    text_preview = line.text[:50] + "..." if len(line.text) > 50 else line.text
    speaker_info = f"{line.speaker}: " if line.speaker else ""
    
    line.delete()
    
    return f"Successfully deleted line #{line_id} ({speaker_info}'{text_preview}')."



@tool
def split_script_line(
    line_id: int,
    keep_text: str,
    remaining_text: str,
    target_chunk_id: int,
    keep_text_zh: str = "",
    remaining_text_zh: str = "",
) -> str:
    """Split a long script line into two lines.

    The original line is truncated to keep_text (staying in its current chunk).
    A new line with remaining_text is inserted into target_chunk_id.
    The new line inherits speaker, line_type, and action_note from the original.

    IMPORTANT: Always call get_surrounding_lines first to read the full text.

    Args:
        line_id: The ID of the ScriptLine to split.
        keep_text: The English text to KEEP in the original line.
        remaining_text: The English text to move to the new line.
        target_chunk_id: The chunk ID where the new line should go.
        keep_text_zh: Chinese translation for the kept text (generate one).
        remaining_text_zh: Chinese translation for the remaining text (generate one).
    """
    from scripts.models import ScriptLine
    from audio_slicer.models import AudioChunk

    try:
        line = ScriptLine.objects.get(id=line_id)
    except ScriptLine.DoesNotExist:
        return f"Error: ScriptLine with id={line_id} not found."

    try:
        target_chunk = AudioChunk.objects.get(id=target_chunk_id)
    except AudioChunk.DoesNotExist:
        return f"Error: AudioChunk with id={target_chunk_id} not found."

    original_text = line.text

    # 1. Update the original line (truncate)
    line.text = keep_text
    line.text_zh = keep_text_zh or line.text_zh
    speaker_str = line.speaker or ""
    line.raw_text = f"{speaker_str}: {keep_text}" if speaker_str else keep_text
    line.save()

    # 2. Calculate order for the new line in the target chunk
    #    Auto-detect direction: if moving backward → append at end;
    #    if moving forward → prepend at beginning
    if target_chunk.chunk_index < line.chunk.chunk_index:
        # Moving to PREVIOUS chunk → insert at END
        last_in_target = (
            ScriptLine.objects.filter(chunk=target_chunk)
            .order_by('-order')
            .values_list('order', flat=True)
            .first()
        )
        new_order = (last_in_target + 1.0) if last_in_target is not None else 0.0
    else:
        # Moving to NEXT chunk → insert at BEGINNING
        first_in_target = (
            ScriptLine.objects.filter(chunk=target_chunk)
            .order_by('order')
            .values_list('order', flat=True)
            .first()
        )
        new_order = (first_in_target - 1.0) if first_in_target is not None else 0.0

    # 3. Create the new line
    raw = f"{speaker_str}: {remaining_text}" if speaker_str else remaining_text
    new_line = ScriptLine.objects.create(
        chunk=target_chunk,
        index=-1,
        order=new_order,
        line_type=line.line_type,
        speaker=line.speaker,
        text=remaining_text,
        text_zh=remaining_text_zh,
        action_note=line.action_note,
        raw_text=raw,
    )

    return (
        f"Successfully split line #{line_id}!\n"
        f"  Original (kept): '{keep_text[:60]}...'\n"
        f"  New line #{new_line.id} in chunk #{target_chunk_id}: '{remaining_text[:60]}...'\n"
        f"  New order: {new_order}"
    )


# ── Reader Management Tools ────────────────────────────────────

@tool
def get_reader_context(paragraph_id: Optional[int] = None, annotation_id: Optional[int] = None, radius: int = 2) -> str:
    """Fetch surrounding article paragraphs for context.
    
    Use this BEFORE edit_reader_paragraph or edit_reader_annotation 
    to understand the reading context. One of `paragraph_id` or `annotation_id` must be provided.
    
    Args:
        paragraph_id: The ID of the reference Paragraph.
        annotation_id: The ID of an Annotation (used to find its paragraph if paragraph_id is unknown).
        radius: Number of paragraphs above and below to include.
    """
    from reader.models import Paragraph, Annotation
    
    # If annotation_id is provided, resolve it to paragraph_id
    if annotation_id is not None:
        try:
            anno = Annotation.objects.get(id=annotation_id)
            paragraph_id = anno.paragraph_id
        except Annotation.DoesNotExist:
            return f"Error: Annotation with id={annotation_id} not found."

    if paragraph_id is None:
        return "Error: You must provide either paragraph_id or annotation_id."

    try:
        ref_p = Paragraph.objects.select_related('article').get(id=paragraph_id)
    except Paragraph.DoesNotExist:
        return f"Error: Paragraph with id={paragraph_id} not found."
    
    siblings = Paragraph.objects.filter(article=ref_p.article).order_by('index')
    siblings_list = list(siblings.values_list('id', flat=True))
    try:
        ref_idx = siblings_list.index(ref_p.id)
    except ValueError:
        return f"Error: Could not locate paragraph {paragraph_id} among siblings."
    
    start = max(0, ref_idx - radius)
    end = min(len(siblings_list), ref_idx + radius + 1)
    
    surrounding_ids = siblings_list[start:end]
    surrounding = Paragraph.objects.filter(id__in=surrounding_ids).order_by('index')
    
    lines = []
    for p in surrounding:
        marker = " <<<" if p.id == ref_p.id else ""
        lines.append(f"[PID:{p.id}] {p.content}{' | zh: ' + p.translation if p.translation else ''}{marker}")
    
    return f"Context around Paragraph #{paragraph_id}:\n" + "\n".join(lines)


@tool
def edit_reader_paragraph(
    paragraph_id: int, 
    content: Optional[str] = None, 
    translation: Optional[str] = None,
    re_translate: bool = False
) -> str:
    """Edit the English text or Chinese translation of a reader paragraph.
    
    Args:
        paragraph_id: Int ID of the Paragraph.
        content: The updated English text (if correcting typos).
        translation: The updated Chinese translation.
        re_translate: If True, calls the central batch_translate_paragraphs API 
                   to re-generate translation automatically.
    """
    from reader.models import Paragraph
    try:
        p = Paragraph.objects.get(id=paragraph_id)
        updates = []
        if content is not None and content.strip() != p.content:
            p.content = content.strip()
            updates.append("content")
        
        if translation is not None and translation.strip() != p.translation:
            p.translation = translation.strip()
            updates.append("translation")
            
        p.save()
        
        if re_translate and 'content' in updates:
            from ai_analysis.services import batch_translate_texts
            try:
                res = batch_translate_texts([{"id": p.id, "text": p.content}])
                if res and len(res) > 0 and 'translation' in res[0]:
                    p.translation = res[0]['translation']
                    p.save(update_fields=['translation'])
                    updates.append("auto-translation")
            except Exception as e:
                updates.append(f"(Auto-translation failed: {e})")
                
        return f"Paragraph {paragraph_id} updated. Fields modified: {', '.join(updates)}. Current content: '{p.content[:50]}...'"
    except Paragraph.DoesNotExist:
        return f"Error: Paragraph {paragraph_id} not found."


@tool
def edit_reader_annotation(
    annotation_id: int, 
    selected_text: Optional[str] = None, 
    user_note: Optional[str] = None, 
    annotation_type: Optional[str] = None
) -> str:
    """Edit an existing annotation (highlight) in the reader.
    
    This function updates the annotation and automatically asks the AI 
    to re-generate the analysis (ai_response) based on the new parameters.
    
    Args:
        annotation_id: ID of the Annotation.
        selected_text: The highlighted text (if correcting the bounds).
        user_note: The user's thought/question (Socratic note).
        annotation_type: Enums: 'yellow' (Jargon), 'blue' (Usage), 'pink' (Thought).
    """
    from reader.models import Annotation
    try:
        anno = Annotation.objects.select_related('paragraph', 'paragraph__article').get(id=annotation_id)
        
        changed = False
        if selected_text is not None and selected_text != anno.selected_text:
            anno.selected_text = selected_text
            changed = True
        if user_note is not None and user_note != anno.user_note:
            anno.user_note = user_note
            changed = True
        if annotation_type is not None and annotation_type != anno.annotation_type:
            anno.annotation_type = annotation_type
            changed = True
            
        if changed:
            # Re-trigger AI logic 
            from reader.ai_services import assist_annotation
            from reader.schemas import AnnotationContext
            try:
                domain = anno.paragraph.article.meta_context.get('domain', 'General')
                res = assist_annotation(AnnotationContext(
                    domain=domain,
                    paragraph=anno.paragraph.content,
                    selected_text=anno.selected_text,
                    annotation_type=anno.annotation_type,
                    user_note=anno.user_note or ""
                ))
                anno.ai_response = {"content": res["content"]}
            except Exception as e:
                return f"Annotation {annotation_id} updated partially, but AI re-generation failed: {e}"
                
            anno.save()
            return f"Annotation {annotation_id} updated and AI response regenerated. New text: '{anno.selected_text}', Type: '{anno.annotation_type}'"
        else:
            return f"No changes provided for Annotation {annotation_id}."
            
    except Annotation.DoesNotExist:
        return f"Error: Annotation {annotation_id} not found."


@tool
def delete_reader_annotation(annotation_id: int) -> str:
    """Permanently delete an annotation from the reader."""
    from reader.models import Annotation
    try:
        anno = Annotation.objects.get(id=annotation_id)
        text = anno.selected_text
        anno.delete()
        return f"Annotation {annotation_id} ('{text}') deleted successfully."
    except Annotation.DoesNotExist:
        return f"Error: Annotation {annotation_id} not found."
