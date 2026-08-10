# ADR 001: Book Support Architecture

## Status

Proposed

## Context

The Lingua Workbench currently supports web-based article reading with paragraph-level annotations. Users want to import PDF books and read them in a chapter-based structure, similar to the existing article reading experience.

Key requirements:
1. Import PDF books from local files
2. Extract chapter structure from PDF (bookmarks or text patterns)
3. Organize content into Book > Chapter > Paragraph hierarchy
4. Support the same annotation system as articles
5. Track reading progress across chapters
6. Filter library view by content type (articles vs books)

## Decision

We will implement book support with the following architecture:

### Data Models

1. **Book Model**: Represents a PDF book
   - Stores metadata (title, author, filename)
   - Tracks reading progress (last read chapter/paragraph)
   - Maintains processing status

2. **Chapter Model**: Represents a chapter within a book
   - Links to parent book
   - Stores chapter content and metadata
   - Maintains chapter ordering

3. **Paragraph Model**: Reuse existing paragraph structure
   - Links to chapter instead of article
   - Maintains same annotation capabilities

### PDF Processing

1. **Library Choice**: pdfplumber for text extraction
   - Better text layout preservation
   - Handles tables and complex formatting
   - Good performance for large documents

2. **Chapter Detection Strategy**:
   - Primary: PDF bookmarks/outlines
   - Fallback: Text pattern matching (Roman numerals, "Chapter X" patterns)
   - Default: Single chapter if no structure detected

3. **Processing Pipeline**:
   - Upload PDF to media storage
   - Create Book record with processing status
   - Extract metadata and chapter structure
   - Create Chapter and Paragraph records
   - Update book status to ready

### API Design

1. **Book Endpoints**:
   - `GET /v1/books/` - List user's books
   - `POST /v1/books/upload` - Upload PDF and create book
   - `GET /v1/books/{id}/` - Get book details with chapters
   - `PUT /v1/books/{id}/update-read-position` - Update reading progress
   - `DELETE /v1/books/{id}/` - Delete book and all content

2. **Filtering**:
   - `GET /v1/articles/?type=all` - All content
   - `GET /v1/articles/?type=article` - Only web articles
   - `GET /v1/articles/?type=book` - Only books

### Frontend Implementation

1. **Library View**:
   - Toggle filter: All / Webpages / E-books
   - Different icons for articles vs books
   - Show relevant metadata per type

2. **Book Reading**:
   - Chapter list in sidebar
   - Reading progress tracking
   - Same annotation system as articles

### Task Processing

1. **Huey Tasks**:
   - PDF parsing and chapter extraction
   - Background processing with status updates
   - Retry logic for failed operations

## Consequences

### Positive

1. **Unified Reading Experience**: Same annotation and reading interface for articles and books
2. **Progress Tracking**: Users can continue reading where they left off
3. **Flexible Organization**: Clear hierarchy for book content
4. **Background Processing**: Non-blocking PDF processing
5. **Filtering**: Easy content type separation

### Negative

1. **Storage Requirements**: PDF files require server storage
2. **Processing Time**: Large PDFs may take time to process
3. **Complexity**: Additional models and relationships
4. **Dependencies**: New PDF processing library required

### Risks

1. **PDF Parsing Quality**: Some PDFs may not extract cleanly
2. **Chapter Detection**: Pattern matching may fail for unusual formats
3. **Performance**: Large books with many chapters may impact performance

### Mitigations

1. **Fallback Strategies**: Multiple chapter detection methods
2. **Error Handling**: Clear status reporting and retry mechanisms
3. **Performance Optimization**: Lazy loading and pagination
4. **User Feedback**: Allow manual chapter splitting if needed

## Implementation Plan

### Phase 1: Backend Foundation
1. Create Book and Chapter models
2. Implement PDF processing service
3. Create Huey tasks for background processing
4. Implement Book API endpoints

### Phase 2: Frontend Integration
1. Update library view with filtering
2. Add book upload functionality
3. Implement book reading view
4. Add reading progress tracking

### Phase 3: Testing and Refinement
1. Test with sample PDFs
2. Refine chapter detection algorithms
3. Optimize performance
4. Gather user feedback

## References

- pdfplumber documentation: https://github.com/jsvine/pdfplumber
- Django file uploads: https://docs.djangoproject.com/en/stable/topics/files/
- Huey task queue: https://huey.readthedocs.io/
