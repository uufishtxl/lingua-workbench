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
    
    header = (
        f"Context around line #{line_id} "
        f"(chunk_id={ref_line.chunk_id}, showing {len(lines)} lines):\n"
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
