"""
Management command to build DITA documentation index.

Usage:
    python manage.py build_dita_index
    python manage.py build_dita_index --clear
    python manage.py build_dita_index --dry-run
"""
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Build or rebuild the DITA documentation vector index'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing index before building',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Parse and show chunks without adding to index',
        )
        parser.add_argument(
            '--dita-path',
            type=str,
            default=None,
            help='Custom path to DITA files (defaults to docs/dita)',
        )
    
    def handle(self, *args, **options):
        from doc_assistant.dita_parser import DITAChunker
        from doc_assistant.services import build_index
        
        # Determine DITA path
        if options['dita_path']:
            dita_root = Path(options['dita_path'])
        else:
            # Default: project_root/docs/dita
            dita_root = settings.DITA_DOCS_DIR
        
        if not dita_root.exists():
            self.stderr.write(
                self.style.ERROR(f"DITA directory not found: {dita_root}")
            )
            return
        
        self.stdout.write(f"DITA root: {dita_root}")
        
        if options['dry_run']:
            # Just parse and show chunks
            self.stdout.write("DRY RUN - Parsing DITA files...")
            chunker = DITAChunker(dita_root)
            chunks = chunker.parse_all_files()
            
            self.stdout.write(f"\nFound {len(chunks)} chunks:\n")
            
            for i, chunk in enumerate(chunks[:10], 1):
                self.stdout.write(self.style.SUCCESS(
                    f"\n[{i}] {chunk.title} ({chunk.topic_type}, audience={chunk.audience})"
                ))
                self.stdout.write(f"    File: {chunk.file_path}")
                self.stdout.write(f"    Content preview: {chunk.content[:100]}...")
            
            if len(chunks) > 10:
                self.stdout.write(f"\n... and {len(chunks) - 10} more chunks")
            
            return
        
        # Build the actual index
        self.stdout.write("Building DITA index...")
        
        stats = build_index(
            dita_root=dita_root,
            clear_existing=options['clear'],
        )
        
        self.stdout.write(self.style.SUCCESS(
            f"\nIndex built successfully!"
            f"\n  Chunks processed: {stats['chunks_processed']}"
            f"\n  Chunks added: {stats['chunks_added']}"
            f"\n  Total in index: {stats['total_chunks']}"
            f"\n  Storage: {stats['persist_directory']}"
        ))
