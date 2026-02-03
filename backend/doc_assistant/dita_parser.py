"""
DITA XML Parser and Chunker for RAG System

This module parses DITA XML files and chunks them into semantically meaningful
units suitable for embedding and retrieval.

Key Concepts (for learning chunking):
1. Parse XML structure to extract semantic units (sections, steps, etc.)
2. Preserve metadata (title, topic type, audience) for filtering
3. Create overlapping chunks for better retrieval coverage
"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
from lxml import etree # Python 中最强大的 XML/HTML 解析库
import hashlib


@dataclass
class DITAChunk:
    """A single chunk extracted from a DITA file."""
    id: str                          # Unique chunk ID (hash of content + file)
    content: str                     # The text content for embedding
    title: str                       # Section or topic title
    topic_type: str                  # concept, task, reference, troubleshooting
    audience: str                    # 'all', 'user', 'developer'
    file_path: str                   # Original DITA file path
    section_path: list[str] = field(default_factory=list)  # Breadcrumb: [topic_title, section_title]
    
    def to_metadata(self) -> dict:
        """Convert to metadata dict for vector store."""
        return {
            'id': self.id,
            'title': self.title,
            'topic_type': self.topic_type,
            'audience': self.audience,
            'file_path': self.file_path,
            'section_path': ' > '.join(self.section_path),
        }


class DITAChunker:
    """
    Parse DITA XML files and extract chunks for RAG.
    
    Chunking Strategy:
    - Each <section> becomes a separate chunk
    - Steps in <task> are grouped together
    - Metadata preserved for filtering by audience
    """
    
    # DITA namespaces (usually none, but just in case)
    NAMESPACES = {}
    
    # Topic type inference from DOCTYPE or root element
    TOPIC_TYPES = {
        'concept': 'concept',
        'task': 'task',
        'reference': 'reference',
        'troubleshooting': 'troubleshooting',
        'topic': 'topic',
        'glossentry': 'glossary',
    }
    
    def __init__(self, dita_root: Path):
        """
        Initialize chunker with the DITA root directory.
        
        Args:
            dita_root: Path to docs/dita directory
        """
        self.dita_root = Path(dita_root)
        
    def parse_all_files(self) -> list[DITAChunk]:
        """Parse all DITA files in the directory tree."""
        chunks = []
        
        # Find all .dita files (excluding temp directories)
        for dita_file in self.dita_root.rglob('*.dita'):
            # Skip temp/build directories
            if 'temp' in dita_file.parts or 'out' in dita_file.parts:
                continue
            
            try:
                file_chunks = self.parse_dita_file(dita_file)
                chunks.extend(file_chunks)
            except Exception as e:
                print(f"Error parsing {dita_file}: {e}")
                
        return chunks
    
    def parse_dita_file(self, file_path: Path) -> list[DITAChunk]:
        """
        Parse a single DITA file into chunks.
        
        This is where the chunking magic happens!
        """
        chunks = []
        
        # Parse XML
        tree = etree.parse(str(file_path)) # tree 相当于整本书
        root = tree.getroot() # root 相当于这本书的封面，或者整棵树的主干。比如一个 concept dita 文件，root 就是 concept
        
        # Determine topic type from root element
        topic_type = self._get_topic_type(root)
        
        # Get topic title
        # ./title 表示当前节点的直接子元素
        # .//title 表示当前节点的所有后代元素
        # //title 从根节点开始任意深度查找 title
        topic_title = self._get_text(root.find('.//title'))
        
        # Get audience from root (defaults to 'all')
        topic_audience = root.get('audience', 'all')
        
        # Get shortdesc as part of context
        shortdesc = self._get_text(root.find('.//shortdesc'))
        
        # Find the body element (conbody, taskbody, refbody, etc.)
        body = self._find_body(root)
        
        if body is None:
            # No body, create single chunk from whole topic
            content = self._extract_text(root)
            if content.strip():
                chunks.append(self._create_chunk(
                    content=content,
                    title=topic_title,
                    topic_type=topic_type,
                    audience=topic_audience,
                    file_path=str(file_path.relative_to(self.dita_root)),
                    section_path=[topic_title],
                ))
            return chunks
        
        # Strategy 1: Chunk by <section> elements
        sections = body.findall('.//section')
        
        if sections:
            for section in sections:
                section_title = self._get_text(section.find('title')) or topic_title
                section_audience = section.get('audience', topic_audience)
                
                content = self._extract_text(section)
                if content.strip():
                    # Prepend shortdesc for context
                    if shortdesc:
                        content = f"{shortdesc}\n\n{content}"
                    
                    chunks.append(self._create_chunk(
                        content=content,
                        title=section_title,
                        topic_type=topic_type,
                        audience=section_audience,
                        file_path=str(file_path.relative_to(self.dita_root)),
                        section_path=[topic_title, section_title],
                    ))
        
        # Strategy 2: For tasks, chunk by steps if no sections
        elif topic_type == 'task':
            steps_section = body.find('.//steps')
            if steps_section is not None:
                content = self._extract_steps(steps_section)
                if shortdesc:
                    content = f"{shortdesc}\n\n{content}"
                    
                chunks.append(self._create_chunk(
                    content=content,
                    title=topic_title,
                    topic_type=topic_type,
                    audience=topic_audience,
                    file_path=str(file_path.relative_to(self.dita_root)),
                    section_path=[topic_title],
                ))
        
        # Fallback: whole body as one chunk
        if not chunks:
            content = self._extract_text(body)
            if shortdesc:
                content = f"{shortdesc}\n\n{content}"
                
            if content.strip():
                chunks.append(self._create_chunk(
                    content=content,
                    title=topic_title,
                    topic_type=topic_type,
                    audience=topic_audience,
                    file_path=str(file_path.relative_to(self.dita_root)),
                    section_path=[topic_title],
                ))
        
        return chunks
    
    def _get_topic_type(self, root: etree._Element) -> str:
        """Infer topic type from root element tag."""
        tag = root.tag.lower()
        return self.TOPIC_TYPES.get(tag, 'topic')
    
    def _find_body(self, root: etree._Element) -> Optional[etree._Element]:
        """Find the body element regardless of topic type."""
        body_tags = ['conbody', 'taskbody', 'refbody', 'troublebody', 'body', 'glossBody']
        for tag in body_tags:
            body = root.find(f'.//{tag}')
            if body is not None:
                return body
        return None
    
    def _get_text(self, element: Optional[etree._Element]) -> str:
        """Extract text from an element, or empty string if None."""
        if element is None:
            return ''
        return ''.join(element.itertext()).strip()
    
    def _extract_text(self, element: etree._Element) -> str:
        """
        Extract all text from an element, preserving some structure.
        This converts XML to readable text.
        """
        parts = []
        
        for child in element.iter():
            # Handle list items
            if child.tag == 'li':
                text = ''.join(child.itertext()).strip()
                if text:
                    parts.append(f"• {text}")
            # Handle steps
            elif child.tag == 'step':
                cmd = child.find('cmd')
                if cmd is not None:
                    parts.append(f"• {self._get_text(cmd)}")
            # Handle paragraphs
            elif child.tag == 'p':
                text = ''.join(child.itertext()).strip()
                if text:
                    parts.append(text)
            # Handle titles (for sections)
            elif child.tag == 'title' and child.getparent() == element:
                text = ''.join(child.itertext()).strip()
                if text:
                    parts.append(f"## {text}")
        
        return '\n\n'.join(parts)
    
    def _extract_steps(self, steps_element: etree._Element) -> str:
        """Extract steps from a task."""
        parts = ["Steps:"]
        
        for i, step in enumerate(steps_element.findall('step'), 1):
            cmd = step.find('cmd')
            if cmd is not None:
                parts.append(f"{i}. {self._get_text(cmd)}")
                
            # Include step info if present
            info = step.find('info')
            if info is not None:
                info_text = self._get_text(info)
                if info_text:
                    parts.append(f"   {info_text}")
        
        return '\n'.join(parts)
    
    def _create_chunk(
        self,
        content: str,
        title: str,
        topic_type: str,
        audience: str,
        file_path: str,
        section_path: list[str],
    ) -> DITAChunk:
        """Create a chunk with a unique ID."""
        # Generate unique ID from file path + section path + content hash
        # Using full content for better uniqueness
        unique_string = f"{file_path}:{':'.join(section_path)}:{content}"
        chunk_id = hashlib.md5(unique_string.encode()).hexdigest()
        
        return DITAChunk(
            id=chunk_id,
            content=content,
            title=title,
            topic_type=topic_type,
            audience=audience,
            file_path=file_path,
            section_path=section_path,
        )
