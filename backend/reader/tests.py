from django.test import TestCase
from django.contrib.auth.models import User
from .models import Book, Chapter


class BookModelTest(TestCase):
    """Test Book model functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_create_book(self):
        """Test creating a book with basic fields."""
        book = Book.objects.create(
            user=self.user,
            title='The English Patient',
            author='Michael Ondaatje',
            original_filename='The English Patient.pdf'
        )
        
        self.assertEqual(book.title, 'The English Patient')
        self.assertEqual(book.author, 'Michael Ondaatje')
        self.assertEqual(book.original_filename, 'The English Patient.pdf')
        self.assertEqual(book.user, self.user)
        self.assertEqual(book.status, 'processing')
        self.assertIsNotNone(book.created_at)
        self.assertIsNotNone(book.updated_at)
    
    def test_book_str_representation(self):
        """Test book string representation."""
        book = Book.objects.create(
            user=self.user,
            title='The English Patient',
            original_filename='The English Patient.pdf'
        )
        
        expected = 'The English Patient (Processing)'
        self.assertEqual(str(book), expected)
    
    def test_book_default_status(self):
        """Test book default status is 'processing'."""
        book = Book.objects.create(
            user=self.user,
            title='Test Book',
            original_filename='test.pdf'
        )
        
        self.assertEqual(book.status, 'processing')
    
    def test_book_status_choices(self):
        """Test book status choices are valid."""
        book = Book.objects.create(
            user=self.user,
            title='Test Book',
            original_filename='test.pdf'
        )
        
        # Test all valid status choices
        valid_statuses = ['processing', 'ready', 'failed']
        for status in valid_statuses:
            book.status = status
            book.save()
            book.refresh_from_db()
            self.assertEqual(book.status, status)


class ChapterModelTest(TestCase):
    """Test Chapter model functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.book = Book.objects.create(
            user=self.user,
            title='The English Patient',
            author='Michael Ondaatje',
            original_filename='The English Patient.pdf'
        )
    
    def test_create_chapter(self):
        """Test creating a chapter with basic fields."""
        chapter = Chapter.objects.create(
            book=self.book,
            title='I  The Villa',
            chapter_index=1,
            start_page=2,
            end_page=10
        )
        
        self.assertEqual(chapter.title, 'I  The Villa')
        self.assertEqual(chapter.chapter_index, 1)
        self.assertEqual(chapter.start_page, 2)
        self.assertEqual(chapter.end_page, 10)
        self.assertEqual(chapter.book, self.book)
        self.assertEqual(chapter.status, 'processing')
    
    def test_chapter_str_representation(self):
        """Test chapter string representation."""
        chapter = Chapter.objects.create(
            book=self.book,
            title='I  The Villa',
            chapter_index=1,
            start_page=2,
            end_page=10
        )
        
        expected = 'The English Patient - Chapter 1: I  The Villa'
        self.assertEqual(str(chapter), expected)
    
    def test_chapter_ordering(self):
        """Test chapters are ordered by chapter_index."""
        chapter3 = Chapter.objects.create(
            book=self.book,
            title='Chapter 3',
            chapter_index=3,
            start_page=20,
            end_page=30
        )
        chapter1 = Chapter.objects.create(
            book=self.book,
            title='Chapter 1',
            chapter_index=1,
            start_page=1,
            end_page=10
        )
        chapter2 = Chapter.objects.create(
            book=self.book,
            title='Chapter 2',
            chapter_index=2,
            start_page=11,
            end_page=19
        )
        
        chapters = list(self.book.chapters.all())
        self.assertEqual(chapters[0], chapter1)
        self.assertEqual(chapters[1], chapter2)
        self.assertEqual(chapters[2], chapter3)
    
    def test_chapter_default_status(self):
        """Test chapter default status is 'processing'."""
        chapter = Chapter.objects.create(
            book=self.book,
            title='Test Chapter',
            chapter_index=1,
            start_page=1,
            end_page=10
        )
        
        self.assertEqual(chapter.status, 'processing')
