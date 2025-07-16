# AskScribe - Intelligent Document Analysis System

## Overview

AskScribe is a Flask-based web application that enables users to upload documents (PDF, DOCX, TXT) and ask natural language questions about their content. The system uses Retrieval-Augmented Generation (RAG) with FAISS vector search and Google Gemini AI to provide intelligent, context-aware answers.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Framework**: Bootstrap 5.3.2 with dark theme
- **Styling**: Custom CSS with ChatGPT-inspired dark interface
- **JavaScript**: Vanilla JS with Bootstrap components
- **Templates**: Jinja2 templating engine
- **Features**: Responsive design, file upload validation, real-time chat interface

### Backend Architecture
- **Framework**: Flask with SQLAlchemy ORM
- **Authentication**: Flask-Login for session management
- **Database**: SQLite with SQLAlchemy (configurable via DATABASE_URL)
- **File Processing**: Multi-format document processing with OCR support
- **AI Integration**: Google Gemini 2.5 Flash model
- **Vector Search**: FAISS for efficient similarity search

## Key Components

### Document Processing Pipeline
- **Text Extraction**: Full support for PDF (PyMuPDF), DOCX (python-docx), and TXT files
- **OCR Support**: Automatic Tesseract OCR for scanned PDFs with minimal text
- **Text Chunking**: Simple text splitter (1000 chars, 200 overlap)
- **Embeddings**: Custom TF-IDF implementation for lightweight vector search

### RAG Engine
- **Vector Store**: Simple TF-IDF-based similarity search
- **Persistence**: JSON-based index storage with document mappings
- **Retrieval**: Context-aware document chunk retrieval using cosine similarity
- **Generation**: Structured prompting with Gemini AI

### Authentication System
- **User Management**: Registration, login, logout with password hashing
- **Session Handling**: Flask-Login with secure session management
- **Authorization**: Route protection for authenticated users only

### Chat System
- **Multi-Session**: Users can create multiple chat sessions
- **Persistent History**: Chat messages stored in database
- **Document Context**: Questions answered using uploaded document content

## Data Flow

1. **Document Upload**:
   - User uploads document → File validation → Secure storage
   - Text extraction → Chunking → Embedding generation
   - Vector storage in FAISS index → Database metadata update

2. **Question Processing**:
   - User asks question → Generate question embedding
   - FAISS similarity search → Retrieve relevant chunks
   - Context preparation → Gemini AI generation → Structured response

3. **Chat Management**:
   - Session creation/selection → Message storage
   - Real-time interface updates → Persistent chat history

## External Dependencies

### AI Services
- **Google Gemini API**: Primary LLM for answer generation with 2.5 Flash model
- **Custom TF-IDF**: Lightweight text similarity without external ML dependencies

### Document Processing
- **PyMuPDF (fitz)**: PDF text extraction and rendering
- **python-docx**: DOCX document processing
- **Tesseract OCR**: Optical character recognition for scanned documents
- **Pillow**: Image processing for OCR pipeline

### Vector Database
- **Custom Implementation**: Simple TF-IDF-based text similarity for lightweight operation
- **JSON Storage**: Persistent document embeddings and chunk mappings

### Web Framework
- **Flask**: Core web framework with extensions
- **SQLAlchemy**: Database ORM and migrations
- **Bootstrap**: Frontend UI framework

## Deployment Strategy

### Environment Configuration
- **Development**: SQLite database, debug mode enabled
- **Production**: Configurable database via DATABASE_URL
- **Security**: Environment-based secrets (GEMINI_API_KEY, SESSION_SECRET)

### File Storage
- **Upload Directory**: Local filesystem storage for documents
- **Vector Store**: Persistent FAISS index with metadata mapping
- **Scalability**: Ready for cloud storage integration (S3, GCS)

### Performance Considerations
- **Database**: Connection pooling and pre-ping for reliability
- **File Limits**: 16MB maximum upload size
- **Vector Search**: In-memory FAISS index for fast retrieval
- **AI Calls**: Optimized prompting for cost-effective Gemini usage

### Security Features
- **File Validation**: Strict file type and size restrictions
- **Path Security**: Secure filename handling and storage
- **Session Management**: Secure session cookies and CSRF protection
- **Proxy Support**: ProxyFix middleware for deployment behind reverse proxy