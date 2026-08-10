from huey.contrib.djhuey import db_task
import logging
import re
from .models import Article, Paragraph, Book, Chapter
from .ai_services import analyze_article_meta
from ai_analysis.services import batch_translate_texts

logger = logging.getLogger(__name__)

@db_task(retries=3, retry_delay=10)
def process_article_meta_task(article_id: int):
    logger.info(f"Starting meta analysis task for Article {article_id}")
    try:
        article = Article.objects.get(id=article_id)
        
        paragraphs = list(article.paragraphs.all())
        
        # Combine title and text with paragraph IDs for context
        text_with_ids = "\n".join([f"[{p.id}] {p.content}" for p in paragraphs])
        full_text = f"TITLE: {article.title}\n{text_with_ids}"
        
        result = analyze_article_meta(title=article.title, text=full_text)
        
        # Save output dictionary to JSONField (status turns translating)
        article.meta_context = result
        article.status = 'translating'
        article.save()
        
        # Trigger paragraph translation in chunks
        chunk_size = 20
        for i in range(0, len(paragraphs), chunk_size):
            chunk = paragraphs[i:i+chunk_size]
            payload = [{"id": p.id, "text": p.content} for p in chunk]
            try:
                translations = batch_translate_texts(payload)
                trans_map = {item['id']: item.get('translation', '') for item in translations if 'id' in item}
                for p in chunk:
                    if p.id in trans_map:
                        p.translation = trans_map[p.id]
                        p.save(update_fields=['translation'])
            except Exception as e:
                logger.error(f"Error translating chunk: {e}")
        
        
        # Mark as completely ready
        article.status = 'ready'
        article.save()
        
        logger.info(f"Successfully processed Article {article_id}")
    except Article.DoesNotExist:
        logger.error(f"Article {article_id} not found.")
    # Removed the catch-all Exception block to allow Huey retries to function.
    # Huey will only mark the task as failed (and stop retrying) after 3 attempts.


@db_task(retries=3, retry_delay=10)
def process_book_task(book_id: int):
    """Process uploaded PDF: extract chapters and create paragraphs."""
    logger.info(f"Starting book processing task for Book {book_id}")
    try:
        import pdfplumber
        
        book = Book.objects.get(id=book_id)
        
        if not book.pdf_file:
            book.status = 'failed'
            book.save()
            logger.error(f"Book {book_id} has no PDF file attached.")
            return
        
        logger.info(f"Opening PDF: {book.pdf_file.path}")
        
        # Step 1: Extract chapter structure
        chapters_info = []
        
        with pdfplumber.open(book.pdf_file.path) as pdf:
            total_pages = len(pdf.pages)
            logger.info(f"PDF has {total_pages} pages")
            
            # Try to extract bookmarks/outlines first
            outlines = pdf.outline if hasattr(pdf, 'outline') else []
            
            if outlines:
                logger.info(f"Found {len(outlines)} bookmarks")
                # Parse bookmarks into chapter structure
                chapters_info = _parse_bookmarks(outlines, total_pages)
            
            if not chapters_info:
                logger.info("No bookmarks found, detecting chapters from text...")
                # Fallback: detect chapter patterns from text
                chapters_info = _detect_chapters_from_text(pdf)
            
            if not chapters_info:
                logger.info("No chapters detected, treating as single chapter")
                # Default: treat entire book as one chapter
                chapters_info = [{
                    'title': book.title or 'Full Book',
                    'start_page': 1,
                    'end_page': total_pages
                }]
            
            logger.info(f"Detected {len(chapters_info)} chapters")
            
            # Step 2: Create Chapter and Paragraph records
            for idx, chapter_info in enumerate(chapters_info):
                logger.info(f"Processing chapter {idx+1}/{len(chapters_info)}: {chapter_info['title']}")
                
                chapter = Chapter.objects.create(
                    book=book,
                    title=chapter_info['title'],
                    chapter_index=idx,
                    start_page=chapter_info['start_page'],
                    end_page=chapter_info['end_page'],
                    status='processing'
                )
                
                # Get the line number where chapter title starts (if available)
                start_line = chapter_info.get('start_line', 0)
                end_line = chapter_info.get('end_line', None)
                
                # Extract text from pages in this chapter
                start_page = chapter_info['start_page'] - 1  # 0-indexed
                end_page = min(chapter_info['end_page'], total_pages)
                
                # Collect page texts, handling chapter boundaries
                page_texts = []
                for page_num in range(start_page, end_page):
                    page = pdf.pages[page_num]
                    text = page.extract_text()
                    if not text:
                        continue
                    
                    # For the first page of chapter, skip lines before chapter title
                    if page_num == start_page and start_line > 0:
                        lines = text.split('\n')
                        # Keep only from chapter title line onwards
                        text = '\n'.join(lines[start_line:])
                    
                    # For the last page of chapter, only include lines before next chapter
                    if page_num == end_page - 1 and end_line is not None and end_line > 0:
                        lines = text.split('\n')
                        # Keep only lines before the next chapter title
                        text = '\n'.join(lines[:end_line])
                    
                    if text.strip():
                        page_texts.append(text)
                
                # Detect recurring headers/footers across pages
                header_footer_lines = _detect_repeated_lines(page_texts)
                logger.info(f"Detected {len(header_footer_lines)} recurring header/footer lines")
                
                # Merge all page text, removing headers/footers by regex
                # We need to pass pages as objects for _merge_page_texts
                merged_text = _merge_page_texts(pdf.pages[start_page:end_page], header_footer_lines, start_line_offset=start_line, end_line_offset=end_line)
                
                # Split into paragraphs (preserving cross-page continuity)
                text_chunks = _split_into_paragraphs(merged_text)
                
                # Bulk create Paragraph objects for better performance
                paragraphs = []
                for p_index, content in enumerate(text_chunks):
                    paragraphs.append(Paragraph(
                        chapter=chapter,
                        index=p_index,
                        content=content
                    ))
                
                if paragraphs:
                    Paragraph.objects.bulk_create(paragraphs)
                    logger.info(f"Created {len(paragraphs)} paragraphs for chapter '{chapter.title}'")
                
                chapter.status = 'ready'
                chapter.save()
        
        # Step 3: Translate all paragraphs in chunks (temporarily disabled)
        # book.status = 'translating'
        # book.save()
        # 
        # all_paragraphs = list(Paragraph.objects.filter(chapter__book=book).order_by('chapter__chapter_index', 'index'))
        # logger.info(f"Translating {len(all_paragraphs)} paragraphs in chunks of 30")
        # 
        # chunk_size = 30
        # for i in range(0, len(all_paragraphs), chunk_size):
        #     chunk = all_paragraphs[i:i+chunk_size]
        #     payload = [{"id": p.id, "text": p.content} for p in chunk]
        #     logger.info(f"Translating chunk {i//chunk_size + 1}, payload size: {len(payload)}, first id: {payload[0]['id'] if payload else 'N/A'}")
        #     
        #     try:
        #         translations = batch_translate_texts(payload)
        #         logger.info(f"Translation response: {len(translations)} items, sample: {translations[:2] if translations else 'empty'}")
        #         
        #         trans_map = {item['id']: item.get('translation', '') for item in translations if 'id' in item}
        #         logger.info(f"Translation map has {len(trans_map)} entries")
        #         
        #         updated_count = 0
        #         for p in chunk:
        #             if p.id in trans_map:
        #                 p.translation = trans_map[p.id]
        #                 p.save(update_fields=['translation'])
        #                 updated_count += 1
        #         
        #         logger.info(f"Updated {updated_count}/{len(chunk)} paragraphs in chunk {i//chunk_size + 1}/{(len(all_paragraphs) + chunk_size - 1)//chunk_size}")
        #     except Exception as e:
        #         logger.error(f"Error translating chunk at offset {i}: {e}")
        #         # Continue with next chunk instead of failing entirely
        
        # Mark book as ready
        book.status = 'ready'
        book.save()
        
        logger.info(f"Successfully processed Book {book_id} with {len(chapters_info)} chapters")
        
    except Book.DoesNotExist:
        logger.error(f"Book {book_id} not found.")
    except Exception as e:
        logger.error(f"Error processing Book {book_id}: {e}")
        try:
            book.status = 'failed'
            book.save()
        except:
            pass
        raise  # Re-raise for Huey retry


def _detect_repeated_lines(page_texts: list[str], min_occurrences: int = 3) -> set[str]:
    """
    Detect lines that appear repeatedly across pages (likely headers/footers).
    Returns a set of normalized lines to filter out.
    """
    from collections import Counter
    
    line_counts = Counter()
    
    for text in page_texts:
        lines = text.split('\n')
        # Check first 3 and last 3 lines (typical header/footer positions)
        candidates = lines[:3] + lines[-3:] if len(lines) > 6 else lines
        for line in candidates:
            normalized = line.strip()
            if normalized and len(normalized) > 5:  # Skip very short lines
                line_counts[normalized] += 1
    
    # Also detect common header/footer patterns
    header_footer_patterns = [
        r'第\s*\d+\s*页\s*共\s*\d+\s*页',  # 第 X 页 共 Y 页
        r'Page\s+\d+\s+of\s+\d+',  # Page X of Y
        r'https?://\S+',  # URLs
        r'www\.\S+',  # www URLs
        r'^\d+$',  # Just page numbers
        r'^[-–—]\s*\d+\s*[-–—]$',  # - 5 - style page numbers
    ]
    
    repeated = set()
    
    # Lines appearing on multiple pages
    for line, count in line_counts.items():
        if count >= min_occurrences:
            repeated.add(line)
    
    # Lines matching known patterns
    for text in page_texts:
        for line in text.split('\n'):
            stripped = line.strip()
            for pattern in header_footer_patterns:
                if re.match(pattern, stripped):
                    repeated.add(stripped)
                    break
    
    return repeated


def _merge_page_texts(pages: list, header_footer_lines: set[str], start_line_offset: int = 0, end_line_offset: int = None) -> str:
    """
    Merge page texts into a single string, removing headers/footers.
    
    Args:
        pages: List of pdfplumber page objects
        header_footer_lines: Set of recurring header/footer lines to remove
        start_line_offset: For the first page, skip lines before this index (chapter title starts here)
        end_line_offset: For the last page, only include lines before this index (next chapter starts here)
    
    Cross-page paragraph merging:
    - Check if a page ends with incomplete sentence (no .!?。！？...)
    - If so, merge the beginning of next page into the same paragraph
    """
    # Patterns to remove (页眉/页脚/网址等)
    cleanup_patterns = [
        r'\s*第\s*\d+\s*页\s*共\s*\d+\s*页[^\n]*',   # 第 X 页 共 Y 页 及其后面到行尾
        r'\s*Page\s+\d+\s+of\s+\d+[^\n]*',              # Page X of Y
        r'https?://\S+',                                      # URLs
        r'www\.[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',               # www.xxx.com
        r'原版英语阅读网',                                      # 网站名
    ]
    
    # Sentence-ending punctuation (Chinese and English)
    sentence_end_pattern = r'[.!?。！？\u2026][\'\"\)\]\s]*$'
    
    cleaned_pages = []
    
    for i, page in enumerate(pages):
        text = page.extract_text()
        if not text:
            continue
        
        # For the first page, skip lines before chapter title
        if i == 0 and start_line_offset > 0:
            lines = text.split('\n')
            text = '\n'.join(lines[start_line_offset:])
        
        # For the last page, only include lines before next chapter
        if i == len(pages) - 1 and end_line_offset is not None and end_line_offset > 0:
            lines = text.split('\n')
            text = '\n'.join(lines[:end_line_offset])
        
        # Apply all cleanup patterns
        for pattern in cleanup_patterns:
            text = re.sub(pattern, '', text, flags=re.MULTILINE)
        
        # Remove detected recurring lines
        for line in header_footer_lines:
            text = text.replace(line, '')
        
        if text.strip():
            cleaned_pages.append(text)
    
    if not cleaned_pages:
        return ''
    
    # Cross-page paragraph merging
    # Check if a page ends with incomplete sentence
    # If so, merge the beginning of next page into the same paragraph
    merged_paragraphs = []
    
    for i, page_text in enumerate(cleaned_pages):
        if i == 0:
            merged_paragraphs.append(page_text)
            continue
        
        # Get the last line of previous page
        prev_text = merged_paragraphs[-1]
        prev_lines = prev_text.rstrip().split('\n')
        last_line = prev_lines[-1].strip() if prev_lines else ''
        
        # Get the first line of current page
        curr_lines = page_text.strip().split('\n')
        first_line = curr_lines[0].strip() if curr_lines else ''
        
        # Check if previous page ends with incomplete sentence
        should_merge = False
        
        if last_line and first_line:
            # Previous line doesn't end with sentence-ending punctuation
            if not re.search(sentence_end_pattern, last_line):
                # Check if first line of current page is a chapter title
                chapter_title_patterns = [
                    r'^[IVX]+\s+[A-Z]',
                    r'^[IVX]+\s*$',
                    r'^Chapter\s+\d+',
                    r'^CHAPTER\s+\d+',
                    r'^Part\s+\d+',
                    r'^PART\s+\d+',
                ]
                is_chapter_title = any(re.match(p, first_line.strip()) for p in chapter_title_patterns)
                
                if not is_chapter_title:
                    should_merge = True
        
        if should_merge:
            # Merge: remove the newline between pages
            merged_paragraphs[-1] = prev_text.rstrip() + ' ' + page_text.lstrip()
        else:
            merged_paragraphs.append(page_text)
    
    # Join with double newline to preserve paragraph boundaries
    return '\n\n'.join(merged_paragraphs)


def _split_into_paragraphs(text: str) -> list[str]:
    """
    Split merged text into clean paragraphs.
    
    Strategy:
    1. Always split by newlines (single or double)
    2. Each line ending with sentence-ending punctuation is a paragraph
    3. Lines without ending punctuation are joined with next line
    4. Chapter titles always start new paragraphs
    """
    # Sentence-ending punctuation (Chinese and English)
    sentence_end_pattern = r'[.!?。！？\u2026][\'\"\)\]\s]*$'
    
    # Chapter title patterns
    chapter_patterns = [
        r'^[IVX]+\s+[A-Z]',
        r'^[IVX]+\s*$',
        r'^Chapter\s+\d+',
        r'^CHAPTER\s+\d+',
        r'^Part\s+\d+',
        r'^PART\s+\d+',
    ]
    
    # Always split by any newlines
    lines = text.split('\n')
    
    # Rebuild paragraphs by detecting boundaries
    rebuilt_paragraphs = []
    current_para = []
    
    for line in lines:
        line_stripped = line.strip()
        if not line_stripped:
            # Empty line = paragraph boundary
            if current_para:
                rebuilt_paragraphs.append('\n'.join(current_para))
                current_para = []
            continue
        
        # If this line is a chapter title, start new paragraph
        if any(re.match(p, line_stripped) for p in chapter_patterns):
            if current_para:
                rebuilt_paragraphs.append('\n'.join(current_para))
                current_para = []
            current_para.append(line)
            continue
        
        # If previous line ended with sentence-ending punctuation,
        # this line starts a new paragraph
        if current_para:
            prev_line = current_para[-1].strip()
            if prev_line and re.search(sentence_end_pattern, prev_line):
                # Previous line is complete, start new paragraph
                rebuilt_paragraphs.append('\n'.join(current_para))
                current_para = []
        
        current_para.append(line)
    
    if current_para:
        rebuilt_paragraphs.append('\n'.join(current_para))
    
    result = []
    for p_text in rebuilt_paragraphs:
        # Clean up whitespace within paragraph
        p_text = re.sub(r'\n', ' ', p_text)
        p_text = re.sub(r'\s+', ' ', p_text)
        p_text = p_text.strip()
        
        if not p_text:
            continue
        
        # Check if this paragraph contains a chapter title followed by text
        # If so, split them
        parts = _split_chapter_from_content(p_text, chapter_patterns)
        
        for part in parts:
            part = part.strip()
            # Keep all non-empty parts (don't filter by length)
            if part:
                result.append(part)
    
    return result


def _split_chapter_from_content(text: str, chapter_patterns: list[str]) -> list[str]:
    """
    Split text that contains a chapter title followed by content.
    e.g., "I The Villa SHE STANDS UP..." -> ["I The Villa", "SHE STANDS UP..."]
    """
    # Chapter title prefix patterns (just the beginning part)
    title_prefix_patterns = [
        (r'^([IVX]+)\s+', 'roman'),           # Roman numeral + space
        (r'^(Chapter\s+\d+)', 'chapter'),     # Chapter N
        (r'^(CHAPTER\s+\d+)', 'chapter'),     # CHAPTER N
        (r'^(Part\s+\d+)', 'part'),           # Part N
        (r'^(PART\s+\d+)', 'part'),           # PART N
        (r'^(\d+\.)', 'number'),              # 1.
    ]
    
    for prefix_pattern, pattern_type in title_prefix_patterns:
        match = re.match(prefix_pattern, text)
        if match:
            prefix_end = match.end()
            prefix = match.group(1)
            remaining = text[prefix_end:]
            
            if not remaining:
                return [text]
            
            # Strategy 1: Look for ALL CAPS content after title
            # e.g., "I The Villa SHE STANDS UP" -> title: "I The Villa", content: "SHE STANDS UP"
            all_caps_match = re.match(
                r'^(.+?)\s+([A-Z]{2,}[A-Z\s]*[A-Z]+)\s+(.+)$',
                remaining
            )
            
            if all_caps_match:
                title_part = all_caps_match.group(1).strip()
                caps_part = all_caps_match.group(2).strip()
                rest_part = all_caps_match.group(3).strip()
                full_title = f"{prefix} {title_part}"
                full_content = f"{caps_part} {rest_part}"
                return [full_title, full_content]
            
            # Strategy 2: Title is typically short (< 50 chars)
            # Try to find a reasonable split point
            words = remaining.split()
            if len(words) > 3:
                # Try different split points
                for i in range(2, min(6, len(words))):
                    candidate_title = ' '.join(words[:i])
                    candidate_content = ' '.join(words[i:])
                    
                    # Check if this is a reasonable split
                    # Title should be title case or short
                    # Content should start with capital letter
                    if (candidate_content and 
                        candidate_content[0].isupper() and 
                        len(candidate_title) < 50):
                        full_title = f"{prefix} {candidate_title}"
                        return [full_title, candidate_content]
            
            # If we can't clearly split, return as is
            return [text]
    
    # No chapter title found, return as is
    return [text]


def _build_chapter_title(match, pattern):
    """
    Build a clean chapter title from regex match.
    
    Args:
        match: The regex match object
        pattern: The pattern string that matched
    
    Returns:
        Clean title string or None if invalid
    """
    full_text = match.group(0).strip()
    
    # Clean up multiple spaces - normalize to single space for consistency
    title = re.sub(r'\s{2,}', ' ', full_text)
    
    # Skip if title is too short (likely false positive)
    if len(title) < 1:
        return None
    
    # For patterns that only captured Roman numerals (no title)
    # e.g., "I", "II", "III"
    # These are valid chapter markers - use them as is
    if re.match(r'^[IVX]+$', title):
        # This is a valid chapter marker (just Roman numeral)
        return title
    
    # Allow "Chapter N" and "Part N" titles (they're valid chapter markers)
    # Just clean them up
    
    return title


def _parse_bookmarks(outlines, total_pages):
    """Parse PDF bookmarks into chapter structure."""
    chapters = []
    
    def _extract_items(items, level=0):
        for item in items:
            if isinstance(item, list):
                _extract_items(item, level + 1)
            else:
                # item is a Destination or similar
                try:
                    title = item.get('title', '') if isinstance(item, dict) else str(item.title)
                    page_num = item.get('page', 0) if isinstance(item, dict) else item.page_number
                    if title and page_num is not None:
                        chapters.append({
                            'title': title,
                            'start_page': page_num + 1,  # pdfplumber uses 0-indexed
                            'level': level
                        })
                except Exception as e:
                    logger.warning(f"Failed to parse bookmark: {e}")
    
    try:
        _extract_items(outlines)
    except Exception as e:
        logger.warning(f"Failed to parse outlines: {e}")
        return []
    
    if not chapters:
        return []
    
    # Sort by page number and set end pages
    chapters.sort(key=lambda x: x['start_page'])
    for i in range(len(chapters) - 1):
        chapters[i]['end_page'] = chapters[i + 1]['start_page'] - 1
    chapters[-1]['end_page'] = total_pages
    
    # Only keep top-level chapters (level 0)
    top_level = [c for c in chapters if c['level'] == 0]
    return [{'title': c['title'], 'start_page': c['start_page'], 'end_page': c['end_page']} for c in top_level]


def _detect_chapters_from_text(pdf):
    """Detect chapter patterns from PDF text - only scan first few lines of each page."""
    chapters = []
    # Common patterns for chapter detection
    # Order matters: more specific patterns first
    # Only match clear chapter markers, not arbitrary text
    patterns = [
        # Roman numerals with title: "I  The Villa", "II The Euclidean Man", "XIII Final Chapter"
        # Pattern: Roman numeral + space(s) + title starting with uppercase letter
        # Title must be 3-50 chars, can contain letters, numbers, spaces, commas, hyphens, apostrophes
        r'^\s*([IVX]+)\s{1,3}([A-Z][a-zA-Z0-9\s,\'\-]{2,49})$',
        # Roman numerals alone on a line (title might be on next line)
        r'^\s*([IVX]+)\s*$',
        # "Chapter N" or "Chapter N: Title"
        r'^\s*Chapter\s+(\d+)(?:[:\s]+([A-Z][a-zA-Z0-9\s,\'\-]{2,49}))?$',
        r'^\s*CHAPTER\s+(\d+)(?:[:\s]+([A-Z][a-zA-Z0-9\s,\'\-]{2,49}))?$',
        # "Part N" or "Part N: Title"
        r'^\s*Part\s+(\d+)(?:[:\s]+([A-Z][a-zA-Z0-9\s,\'\-]{2,49}))?$',
        r'^\s*PART\s+(\d+)(?:[:\s]+([A-Z][a-zA-Z0-9\s,\'\-]{2,49}))?$',
    ]
    
    # Patterns to EXCLUDE (not chapters)
    exclude_patterns = [
        r'^\d{4}[\./-]',  # Dates like "1930." or "1930/"
        r'^\d+\.\s+[a-z]',  # Numbered lists like "1. a container"
        r'^\d+\.\s+[A-Z][a-z]+\s+(?:a|an|the|is|was|are|were)',  # Sentences starting with numbers
        r'^\d+\.\s+[A-Z][a-z]+.*\.$',  # Sentences ending with period (definitions)
    ]
    
    total_pages = len(pdf.pages)
    logger.info(f"Scanning {total_pages} pages for chapter patterns...")
    
    for page_num, page in enumerate(pdf.pages):
        # Extract text from page
        text = page.extract_text(x_tolerance=3, y_tolerance=3)
        if not text:
            continue
        
        lines = text.split('\n')
        # Scan ALL lines on the page - chapter titles can be anywhere
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # Skip lines that are too long (likely paragraphs, not titles)
            if len(line) > 100:
                continue
            
            # Skip lines that match exclusion patterns
            if any(re.match(p, line) for p in exclude_patterns):
                continue
            
            for pattern in patterns:
                match = re.match(pattern, line)
                if match:
                    # Build a clean title based on the pattern
                    title = _build_chapter_title(match, pattern)
                    if title:
                        # Avoid duplicates on same page
                        if not any(ch['start_page'] == page_num + 1 for ch in chapters):
                            chapters.append({
                                'title': title,
                                'start_page': page_num + 1,
                                'start_line': i  # Record which line the chapter title starts at
                            })
                            logger.info(f"Found chapter: '{title}' at page {page_num + 1} (line {i+1})")
                            break
    
    if not chapters:
        return []
    
    # Remove duplicates (same page)
    seen_pages = set()
    unique_chapters = []
    for ch in chapters:
        if ch['start_page'] not in seen_pages:
            seen_pages.add(ch['start_page'])
            unique_chapters.append(ch)
    
    # Set end pages
    # For each chapter, end_page includes the page where the next chapter starts
    # (because content before the next chapter title belongs to current chapter)
    for i in range(len(unique_chapters) - 1):
        # End page is the same as next chapter's start page
        # The split happens at the line level, not page level
        unique_chapters[i]['end_page'] = unique_chapters[i + 1]['start_page']
        # Store the end_line for the current chapter (line before next chapter title)
        unique_chapters[i]['end_line'] = unique_chapters[i + 1].get('start_line', 0)
    unique_chapters[-1]['end_page'] = total_pages
    unique_chapters[-1]['end_line'] = None  # Last chapter goes to end of page
    
    logger.info(f"Detected {len(unique_chapters)} unique chapters")
    return unique_chapters
