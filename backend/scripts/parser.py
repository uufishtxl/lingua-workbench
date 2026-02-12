"""
Parser for fanfr.com Friends scripts.
Fetches and parses episode scripts into structured ScriptLine data.
"""
import re
import requests
from bs4 import BeautifulSoup
from typing import Optional


def fetch_script_html(season: int, episode: int) -> str:
    """
    Fetch raw HTML from fanfr.com for a given episode.
    URL format: https://www.fanfr.com/scripts/saison{season}/friendsgeneration2.php?nav=script&version=vo&episodescript={season}{episode:02d}
    """
    url = f"https://www.fanfr.com/scripts/saison{season}/friendsgeneration2.php?nav=script&version=vo&episodescript={season}{episode:02d}"
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.text


def parse_script(html: str) -> list[dict]:
    """
    Parse fanfr.com script HTML into structured data.
    
    HTML Structure observed:
    - Scene headers: <h3>[Scene: ...]</h3>
    - Dialogues: <p><b>Speaker</b>: text</p> or <p><b>Speaker</b>; text</p>
    - Actions: <p>(action text)</p> without <b> tag
    
    Returns:
        list of dicts with keys:
        - type: 'scene' | 'dialogue' | 'action'
        - speaker: str (only for dialogue)
        - text: str (clean text without action notes)
        - action_note: str (only for dialogue with inline actions)
        - raw_text: str (original text)
    """
    soup = BeautifulSoup(html, 'html.parser')
    
    # Find the main script content area
    content_div = soup.find('div', class_='contenu') or soup.find('div', id='contenu') or soup.body
    if not content_div:
        return []
    
    lines = []
    
    # Process h3 (scene headers) and p (dialogues/actions) elements
    for element in content_div.find_all(['h3', 'p']):
        # Normalize whitespace: replace all whitespace sequences with single space
        raw_text = ' '.join(element.get_text().split())
        if not raw_text or len(raw_text) < 2:
            continue
        
        # Skip credits/copyright
        if '©' in raw_text or 'Fan Club' in raw_text or 'friendsgeneration' in raw_text.lower():
            continue
        
        # Skip "OPENING CREDITS", "END", etc.
        if raw_text.strip().upper() in ['OPENING CREDITS', 'END', 'CLOSING CREDITS', 'COMMERCIAL BREAK']:
            continue
        
        # Check for scene header
        scene_match = re.match(r'^\[Scene:\s*(.+?)\]$', raw_text, re.IGNORECASE)
        if scene_match:
            lines.append({
                'type': 'scene',
                'speaker': None,
                'text': scene_match.group(1),
                'action_note': None,
                'raw_text': raw_text
            })
            
            # SPECIAL CASE: After h3, there might be a standalone <b> tag with dialogue
            # that's not wrapped in <p>. Look for the next sibling <b> tag.
            next_sib = element.find_next_sibling()
            if next_sib and next_sib.name == 'b':
                speaker = next_sib.get_text(strip=True).rstrip(':')
                # Get all text nodes between this <b> and the next block element
                dialogue_parts = []
                for sib in next_sib.next_siblings:
                    if sib.name in ['h3', 'p', 'b']:
                        break
                    text = sib.get_text() if hasattr(sib, 'get_text') else str(sib)
                    text = text.strip()
                    if text:
                        dialogue_parts.append(text)
                
                if dialogue_parts and speaker:
                    content = ' '.join(dialogue_parts)
                    action_parts = re.findall(r'\(([^)]+)\)', content)
                    action_note = '; '.join(action_parts) if action_parts else None
                    clean_text = re.sub(r'\([^)]*\)\s*', '', content).strip()
                    
                    lines.append({
                        'type': 'dialogue',
                        'speaker': speaker,
                        'text': clean_text,
                        'action_note': action_note,
                        'raw_text': f"{speaker}: {content}"
                    })
            continue
        
        # Check for dialogue: look for <b> tag inside <p>
        if element.name == 'p':
            b_tag = element.find('b')
            if b_tag:
                speaker = b_tag.get_text(strip=True)
                
                # Get the rest of the text after the speaker name
                # Normalize whitespace in full text too
                full_text = ' '.join(element.get_text().split())
                # The text after speaker usually starts with : or ;
                content_match = re.match(rf'^{re.escape(speaker)}[;:]\s*(.*)$', full_text, re.DOTALL)
                
                if content_match and speaker:
                    content = content_match.group(1)
                    
                    # Extract action notes from parentheses
                    action_parts = re.findall(r'\(([^)]+)\)', content)
                    action_note = '; '.join(action_parts) if action_parts else None
                    
                    # Clean text (remove parentheses content)
                    clean_text = re.sub(r'\([^)]*\)\s*', '', content).strip()
                    
                    lines.append({
                        'type': 'dialogue',
                        'speaker': speaker,
                        'text': clean_text,
                        'action_note': action_note,
                        'raw_text': raw_text
                    })
                    continue
        
        # Check for standalone action (text in parentheses without speaker)
        if raw_text.startswith('(') and raw_text.endswith(')'):
            lines.append({
                'type': 'action',
                'speaker': None,
                'text': raw_text[1:-1],  # Remove outer parentheses
                'action_note': None,
                'raw_text': raw_text
            })
            continue
        
        # Fallback: try regex matching for dialogue pattern
        # This handles cases where the HTML structure is different
        # Pattern supports: multi-word names "Mr Zelner", hyphenated "Phoebe-Estelle"
        dialogue_match = re.match(r'^([A-Za-z][A-Za-z\s\-]*?)[;:]\s*(.+)$', raw_text, re.DOTALL)
        if dialogue_match:
            speaker = dialogue_match.group(1).strip()
            content = dialogue_match.group(2)
            
            if len(speaker) > 1 and speaker[0].isupper():
                action_parts = re.findall(r'\(([^)]+)\)', content)
                action_note = '; '.join(action_parts) if action_parts else None
                clean_text = re.sub(r'\([^)]*\)\s*', '', content).strip()
                
                lines.append({
                    'type': 'dialogue',
                    'speaker': speaker,
                    'text': clean_text,
                    'action_note': action_note,
                    'raw_text': raw_text
                })
    
    return lines


def parse_fanfr_script(season: int, episode: int) -> list[dict]:
    """
    Main entry point: fetch and parse a Friends episode script.
    
    Args:
        season: Season number (1-10)
        episode: Episode number
        
    Returns:
        List of parsed script lines
    """
    html = fetch_script_html(season, episode)
    return parse_script(html)
