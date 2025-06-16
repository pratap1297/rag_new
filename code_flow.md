Looking at your RAG system code, I can now provide a comprehensive analysis of the call flow. This is a well-structured enterprise RAG system with multiple components. Let me break down the main call flows:

## System Architecture Overview

The system follows a modular architecture with these key components:
- **FastAPI** for REST API
- **FAISS** for vector storage
- **Multiple embedding providers** (Cohere, Sentence Transformers)
- **Multiple LLM providers** (Groq, OpenAI)
- **Dependency injection** for component management
- **Comprehensive monitoring** (heartbeat, folder monitoring)
- **ServiceNow integration** for ticket management

## Main Call Flows

### 1. **System Initialization Flow** (`main.py`)
```
main.py
├── initialize_system()
│   ├── ConfigManager (loads configuration)
│   ├── DependencyContainer (registers all services)
│   ├── Data directories creation
│   ├── Component initialization:
│   │   ├── JSONStore
│   │   ├── MetadataStore
│   │   ├── FAISSStore
│   │   ├── Embedder
│   │   ├── Chunker
│   │   ├── LLMClient
│   │   ├── Reranker
│   │   ├── QueryEnhancer
│   │   ├── QueryEngine
│   │   └── IngestionEngine
│   └── HeartbeatMonitor initialization
├── create_api_app()
└── Start Uvicorn server
```

### 2. **Document Ingestion Flow**

**File Upload Endpoint** (`/upload`):
```
POST /upload
├── FastAPI receives file
├── IngestionEngine.ingest_file()
│   ├── Check for existing file (delete old vectors if updating)
│   ├── Extract text based on file type (PDF/DOCX/TXT/MD)
│   ├── Chunker.chunk_text()
│   │   ├── SemanticChunker (if enabled)
│   │   └── RecursiveCharacterTextSplitter
│   ├── Embedder.embed_texts()
│   │   ├── Cohere API (if configured)
│   │   └── SentenceTransformers (fallback)
│   ├── FAISSStore.add_vectors()
│   │   ├── Normalize vectors
│   │   ├── Add to FAISS index
│   │   └── Save metadata
│   └── MetadataStore.add_file_metadata()
└── Return response with file_id and stats
```

**Text Ingestion Endpoint** (`/ingest`):
```
POST /ingest
├── Receive text and metadata
├── Similar flow to file upload but without file extraction
└── Return ingestion results
```

### 3. **Query Processing Flow**

**Query Endpoint** (`/query`):
```
POST /query
├── QueryEngine.process_query()
│   ├── QueryEnhancer.enhance_query() (if enabled)
│   │   ├── Detect query intent
│   │   ├── Extract keywords
│   │   ├── Generate query expansions
│   │   └── Create query variants
│   ├── Embedder.embed_text() (for each query variant)
│   ├── FAISSStore.search_with_metadata()
│   │   ├── Normalize query vector
│   │   ├── FAISS similarity search
│   │   └── Filter and format results
│   ├── Reranker.rerank() (if enabled)
│   │   └── Cross-encoder scoring
│   ├── LLMClient.generate()
│   │   ├── Build context from top results
│   │   ├── Create prompt
│   │   └── Call LLM API (Groq/OpenAI)
│   └── Format response with sources
└── Return query response
```

### 4. **ServiceNow Integration Flow**

**Automated Sync Flow**:
```
ServiceNowScheduler (runs every 15 minutes by default)
├── ServiceNowConnector.get_incidents()
│   └── Fetch from ServiceNow API with filters
├── ServiceNowProcessor.process_incidents()
│   ├── Extract technical details
│   ├── Determine if network-related
│   └── Format as ProcessedTicket
├── Cache incidents in SQLite
├── Convert to documents
└── IngestionEngine.ingest_file() for each ticket
```

### 5. **Folder Monitoring Flow**

```
FolderMonitor (runs every 60 seconds by default)
├── Scan monitored folders
├── Detect file changes (new/modified/deleted)
├── For new/modified files:
│   └── IngestionEngine.ingest_file()
└── For deleted files:
    └── FAISSStore.delete_vectors_by_doc_path()
```

### 6. **Health Monitoring Flow**

```
HeartbeatMonitor (runs every 30 seconds)
├── Check API server health
├── Check storage layer
├── Check FAISS vector store
├── Check embedding service
├── Check LLM service
├── Check system resources (CPU/Memory/Disk)
└── Store health history
```

## Key Features and Design Patterns

1. **Dependency Injection**: All components are managed through `DependencyContainer` for loose coupling
2. **Multi-Provider Support**: Supports multiple embedding (Cohere, SentenceTransformers) and LLM providers (Groq, OpenAI)
3. **Advanced Query Processing**: Query enhancement with reformulation and semantic expansion
4. **Reranking**: Optional cross-encoder reranking for better relevance
5. **Comprehensive Error Handling**: Custom exception hierarchy with proper error tracking
6. **Persistent Storage**: Metadata stored in JSON files, vectors in FAISS with backup support
7. **Update Handling**: Smart detection and replacement of existing documents
8. **Monitoring**: Health checks, performance metrics, and folder monitoring

## API Endpoints Summary

**Core Endpoints**:
- `POST /query` - Process queries
- `POST /ingest` - Ingest text
- `POST /upload` - Upload files
- `GET /stats` - System statistics
- `GET /health` - Basic health check
- `GET /health/detailed` - Comprehensive health check

**Management Endpoints** (`/manage/*`):
- Document and vector management
- Cleanup operations
- Metadata updates

**ServiceNow Endpoints** (`/api/servicenow/*`):
- Integration management
- Manual sync
- Configuration

**Monitoring Endpoints**:
- Heartbeat monitoring
- Folder monitoring
- Performance metrics

This is a production-ready RAG system with enterprise features like monitoring, multi-provider support, and external integrations.