# RAG Backend Service

Consolidated Python/Flask backend service for the RAG (Retrieval Augmented Generation) demo. This service combines all RAG operations into a single, unified API.

## 🎉 Now Using ChromaDB!

**Migration Complete**: This backend now uses ChromaDB instead of Milvus for simplified deployment and better Power10 compatibility.

See [CHROMADB_MIGRATION.md](CHROMADB_MIGRATION.md) for migration details.

## Overview

This backend service replaces the previous architecture of 5 separate Flask microservices with a single, consolidated service that handles:

- Collection management (list, drop)
- PDF document loading into vector database
- **Web page scraping and loading** - Load content from IBM Docs pages
- Document search and retrieval
- LLM prompt generation

## 🆕 New Feature: Web Scraping

The backend now supports loading content directly from web pages (especially IBM Docs pages) into the vector database. This allows you to:

- Keep your knowledge base up-to-date with live documentation
- Load IBM announcements and product updates automatically
- Scrape multiple pages at once
- Access dynamic content that was previously unavailable

**See [WEB_SCRAPING_FEATURE.md](WEB_SCRAPING_FEATURE.md) for detailed documentation.**

Quick example:
```bash
curl -X POST http://localhost:8080/api/load-url \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.ibm.com/docs/en/announcements/power-s1014-9105-41b",
    "collection_name": "ibm_announcements"
  }'
```

## Architecture

```
┌─────────────────┐
│   Carbon UI     │
│   (Next.js)     │
└────────┬────────┘
         │
         │ HTTP/REST
         │
┌────────▼────────┐      ┌──────────────┐
│  RAG Backend    │      │  ChromaDB    │
│   (Flask)       │◄────►│  (embedded)  │
└────────┬────────┘      └──────────────┘
         │
         │ HTTP
         │
┌────────▼────────┐
│  LLM Service    │
│  (llama.cpp)    │
└─────────────────┘
```

**Benefits of ChromaDB:**
- ✅ Single service deployment (no etcd, MinIO, Milvus)
- ✅ Embedded database (no network latency)
- ✅ Better Power10 compatibility
- ✅ Simpler deployment (75% fewer services)
- ✅ Lower resource usage (~2-4GB vs ~6GB)

## API Endpoints

### Collection Management

#### List Collections
```bash
GET /api/collections
```

Response:
```json
{
  "success": true,
  "collections": ["demo", "sales_manuals"]
}
```

#### Drop Collection
```bash
DELETE /api/collections/<collection_name>
```

Response:
```json
{
  "success": true,
  "message": "Collection sales_manuals dropped successfully"
}
```

### Document Management

#### Load PDF
```bash
POST /api/load-pdf
Content-Type: application/json

{
  "server_name": "HPE-ProLiant-DL380-Gen11",
  "collection_name": "sales_manuals"
}
```

Response:
```json
{
  "success": true,
  "message": "Successfully loaded HPE-ProLiant-DL380-Gen11",
  "chunks": 42,
  "collection": "sales_manuals"
}
```

#### Load Web Page (NEW)
```bash
POST /api/load-url
Content-Type: application/json

{
  "url": "https://www.ibm.com/docs/en/announcements/power-s1014-9105-41b",
  "collection_name": "ibm_announcements"
}
```

Response:
```json
{
  "success": true,
  "message": "Successfully loaded content from URL",
  "title": "IBM Power S1014 (9105-41B) announcement",
  "chunks": 15,
  "collection": "ibm_announcements",
  "url": "https://www.ibm.com/docs/en/announcements/power-s1014-9105-41b"
}
```

#### Load Multiple Web Pages (NEW)
```bash
POST /api/load-multiple-urls
Content-Type: application/json

{
  "urls": [
    "https://www.ibm.com/docs/en/announcements/power-s1014-9105-41b",
    "https://www.ibm.com/docs/en/announcements/power-s1022-9105-22a"
  ],
  "collection_name": "ibm_announcements"
}
```

Response:
```json
{
  "success": true,
  "message": "Successfully loaded 2 URLs",
  "pages_loaded": 2,
  "total_chunks": 28,
  "collection": "ibm_announcements",
  "titles": [
    "IBM Power S1014 (9105-41B) announcement",
    "IBM Power S1022 (9105-22A) announcement"
  ]
}
```

#### Search Documents
```bash
POST /api/search
Content-Type: application/json

{
  "question": "What are the memory specifications?",
  "collection_name": "sales_manuals",
  "server_name": "HPE-ProLiant-DL380-Gen11",
  "k": 3
}
```

Response:
```json
{
  "success": true,
  "results": [
    {
      "content": "Memory specifications...",
      "metadata": {
        "source": "HPE-ProLiant-DL380-Gen11.pdf",
        "page": 5
      },
      "score": 0.85
    }
  ],
  "count": 3
}
```

### LLM Generation

#### Generate Response
```bash
POST /api/generate
Content-Type: application/json

{
  "prompt": "Based on the following context...",
  "temperature": 0.1,
  "n_predict": 100,
  "stream": false
}
```

Response:
```json
{
  "success": true,
  "content": "The generated response...",
  "timings": {
    "predicted_ms": 1234.56
  }
}
```

### Health Check

```bash
GET /health
```

Response:
```json
{
  "status": "healthy",
  "chromadb": "connected",
  "llm": "connected"
}
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `CHROMA_PERSIST_DIR` | `/app/chroma_db` | ChromaDB data directory |
| `LLAMA_HOST` | `llama-service` | LLM service hostname |
| `LLAMA_PORT` | `8080` | LLM service port |
| `PDF_DIR` | `/app/pdfs` | Directory containing PDF files |
| `CORS_ORIGIN` | `*` | CORS allowed origins |

## OpenShift Deployment

### Quick Deploy (Recommended)

From the `RAG-with-Notebook` directory:

```bash
# Make script executable (Linux/Mac)
chmod +x rag-backend/deploy-chromadb.sh

# Run deployment script
./rag-backend/deploy-chromadb.sh
```

### Manual Deployment

```bash
# 1. Create persistent storage
oc apply -f rag-backend/rag-backend-pvc.yaml

# 2. Build image
cd rag-backend
oc new-build --name rag-backend --binary --strategy docker
oc start-build rag-backend --from-dir=. --follow

# 3. Deploy
oc apply -f rag-backend-deploy.yaml
oc apply -f rag-backend-svc.yaml
oc apply -f rag-backend-route.yaml

# 4. Verify
oc logs -f deployment/rag-backend
oc get route rag-backend
```

### Docker Build (Local Development)

```bash
# Build the image
docker build -t rag-backend:latest .

# Run the container
docker run -d \
  -p 8080:8080 \
  -e CHROMA_PERSIST_DIR=/app/chroma_db \
  -e LLAMA_HOST=llama-service \
  -v /path/to/chroma_db:/app/chroma_db \
  -v /path/to/pdfs:/app/pdfs \
  rag-backend:latest
```

## Local Development

### Prerequisites

- Python 3.12+
- LLM service (llama.cpp) running

### Setup

```bash
# Create virtual environment
python3.12 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export CHROMA_PERSIST_DIR=./chroma_db
export LLAMA_HOST=localhost
export LLAMA_PORT=8080
export PDF_DIR=./pdfs

# Run the application
python app.py
```

The service will start on `http://localhost:8080`

## Dependencies

### Core Framework
- Flask 3.0.0 - Web framework
- flask-cors 4.0.0 - CORS support
- gunicorn 21.2.0 - Production WSGI server

### Vector Database
- chromadb 0.4.22 - ChromaDB embedded vector database

### RAG Framework
- langchain 0.1.0 - LLM application framework
- langchain-community 0.0.10 - Community integrations
- langchain-core 0.1.10 - Core abstractions

### Embeddings
- sentence-transformers 2.2.2 - Sentence embeddings
- transformers 4.36.2 - HuggingFace transformers
- torch 2.1.2 - PyTorch for model inference

### Document Processing
- pypdf 3.17.4 - PDF parsing
- pypdf2 3.0.1 - Additional PDF support

### Web Scraping (NEW)
- beautifulsoup4 4.12.2 - HTML parsing
- lxml 5.1.0 - Fast XML/HTML parser

### Utilities
- requests 2.31.0 - HTTP client
- python-dotenv 1.0.0 - Environment variable management

## Logging

The service uses Python's standard logging module with INFO level by default. Logs include:

- Service startup information
- API request details
- Milvus connection status
- Document processing progress
- Error messages with stack traces

## Error Handling

All endpoints return consistent error responses:

```json
{
  "error": "Detailed error message"
}
```

HTTP status codes:
- `200` - Success
- `400` - Bad request (missing parameters)
- `404` - Resource not found
- `500` - Internal server error
- `503` - Service unavailable (health check)
- `504` - Gateway timeout (LLM timeout)

## Performance Considerations

- **Embeddings Model**: Loaded lazily on first use and cached
- **Gunicorn Workers**: 2 workers with 4 threads each
- **Request Timeout**: 120 seconds for long-running operations
- **LLM Timeout**: 60 seconds for generation requests

## Migration from Previous Architecture

This service replaces:
1. `RAG-List-Collections` → `GET /api/collections`
2. `RAG-Drop-Collection` → `DELETE /api/collections/<name>`
3. `RAG-Loader` → `POST /api/load-pdf`
4. `RAG-Get-Docs` → `POST /api/search`
5. `RAG-Prompt-LLM` → `POST /api/generate`

Benefits:
- Single deployment unit
- Shared embeddings model (memory efficient)
- Consistent error handling
- Unified logging
- Simplified networking (no inter-service communication)

## Testing

```bash
# Health check
curl http://localhost:8080/health

# List collections
curl http://localhost:8080/api/collections

# Load a PDF
curl -X POST http://localhost:8080/api/load-pdf \
  -H "Content-Type: application/json" \
  -d '{"server_name": "test-server", "collection_name": "demo"}'

# Search documents
curl -X POST http://localhost:8080/api/search \
  -H "Content-Type: application/json" \
  -d '{"question": "test query", "collection_name": "demo", "k": 3}'
```

## License

Same as parent project.