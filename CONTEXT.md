# Lingua Workbench - Project Context

## Project Overview

Lingua Workbench is a personal learning platform that combines audio-based language learning with intelligent reading tools. The platform supports multiple learning modalities including audio processing, script management, and advanced reading capabilities with AI-powered annotations.

## Key Domain Terms

- **Drama**: A media series (e.g., TV show, podcast) containing multiple seasons
- **Season**: A collection of episodes within a drama
- **Episode**: A single audio unit within a season
- **Chunk**: A segment of audio for processing
- **Script**: Text content associated with audio
- **Article**: Web-based reading content with paragraphs and annotations
- **Book**: PDF-based reading content with chapters (planned)
- **Chapter**: A section within a book
- **Annotation**: User-created notes on text with AI-powered assistance
- **Paragraph**: A text segment within an article or chapter

## Technical Stack

### Backend
- **Framework**: Django with Django REST Framework
- **Database**: SQLite (development), PostgreSQL (production)
- **Task Queue**: Huey with SQLite backend
- **PDF Processing**: pdfplumber (planned)
- **AI Services**: LLM integration for analysis and translation

### Frontend
- **Framework**: Vue.js 3 with TypeScript
- **UI Library**: Element Plus
- **HTTP Client**: Axios
- **State Management**: Pinia
- **Router**: Vue Router

### Infrastructure
- **Version Control**: Git with GitHub
- **Deployment**: Docker (planned)

## Architecture Overview

The application follows a layered architecture:

1. **Presentation Layer**: Vue.js frontend with responsive UI
2. **API Layer**: Django REST Framework endpoints
3. **Service Layer**: Business logic and AI integration
4. **Data Layer**: Django models with database abstraction
5. **Task Layer**: Huey background tasks for async processing

## Coding Conventions

### Backend (Python/Django)
- Follow PEP 8 style guide
- Use type hints where appropriate
- Document complex functions with docstrings
- Use Django's ORM conventions
- Implement proper error handling and logging

### Frontend (Vue.js/TypeScript)
- Use Composition API with `<script setup>` syntax
- Follow Vue.js style guide
- Use TypeScript for type safety
- Implement proper component organization
- Use Element Plus components consistently

## Key Features

### Audio Processing
- Upload and process audio files
- Extract and manage audio chunks
- Generate and edit scripts
- Support for multiple dramas and seasons

### Reading Tools
- Web article extraction and parsing
- Paragraph-level content organization
- Multi-type annotations (jargon, usage, thought)
- AI-powered annotation assistance
- Bilingual support (English/Chinese)

### AI Integration
- Article meta-analysis (outline, domain detection)
- Batch translation services
- Context-aware annotation responses
- Background processing with Huey tasks

## Development Workflow

1. **Feature Development**: Use vertical slices for complete feature implementation
2. **Testing**: Implement TDD with red-green-refactor cycle
3. **Code Review**: Use PR review process
4. **Deployment**: Containerized deployment with Docker

## Future Roadmap

1. **Book Support**: PDF import and chapter-based reading
2. **Enhanced AI**: More sophisticated analysis and recommendations
3. **Mobile Support**: Progressive Web App (PWA) implementation
4. **Collaboration**: Shared annotations and learning paths
5. **Analytics**: Learning progress tracking and insights
