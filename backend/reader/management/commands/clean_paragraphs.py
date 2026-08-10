"""
Management command to strip ¬ characters from Paragraph content.

Usage:
    python manage.py clean_paragraphs
    python manage.py clean_paragraphs --dry-run   # preview only, no DB writes
"""
from django.core.management.base import BaseCommand
from reader.models import Paragraph


class Command(BaseCommand):
    help = "Remove ¬ characters from Paragraph.content filtered by chapter title."

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Preview changes without writing to DB.')
        parser.add_argument('--list-chapters', action='store_true', help='List all chapter titles and exit.')
        parser.add_argument('--chapter', type=str, default='English Patient', help='Substring to match in BOOK title (case-insensitive). Default: "English Patient"')

    def handle(self, *args, **options):
        if options['list_chapters']:
            from reader.models import Chapter
            for ch in Chapter.objects.select_related('book').all():
                self.stdout.write(f'  Book: {ch.book.title} | Ch#{ch.id} | {ch.title}')
            return

        dry_run = options['dry_run']
        chapter_kw = options['chapter']
        qs = Paragraph.objects.filter(
            chapter__book__title__icontains=chapter_kw,
            content__contains='¬',
        )
        count = qs.count()
        if count == 0:
            self.stdout.write(self.style.WARNING(f'No paragraphs found matching chapter="{chapter_kw}" with ¬.'))
            return

        self.stdout.write(f'Found {count} paragraph(s) containing ¬.')

        if dry_run:
            for p in qs[:10]:
                self.stdout.write(f'  [P#{p.id}] {p.content[:120]}...')
            if count > 10:
                self.stdout.write(f'  ... and {count - 10} more.')
            self.stdout.write(self.style.WARNING('Dry-run mode, no changes written.'))
            return

        updated = 0
        for p in qs.iterator():
            cleaned = p.content.replace('¬', '')
            if cleaned != p.content:
                p.content = cleaned
                p.save(update_fields=['content'])
                updated += 1

        self.stdout.write(self.style.SUCCESS(f'Done. Cleaned {updated} paragraph(s).'))
