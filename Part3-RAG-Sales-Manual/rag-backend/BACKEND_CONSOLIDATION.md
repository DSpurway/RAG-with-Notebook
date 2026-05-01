# Backend Consolidation to OpenSearch

**Date**: April 27, 2026  
**Status**: ✅ Complete

## Overview

The RAG backend has been consolidated to use **OpenSearch only** as the vector database. All ChromaDB and Milvus-related code has been archived.

## Changes Made

### 1. File Consolidation

**Active Files** (OpenSearch-based):
- `app.py` - Main backend application (formerly `app_opensearch.py`)
- `Dockerfile` - Container build configuration (formerly `Dockerfile.opensearch`)
- `requirements.txt` - Python dependencies (formerly `requirements-opensearch.txt`)
- `deploy.sh` / `deploy.ps1` - Deployment scripts (formerly `deploy-opensearch.*`)

**Archived Files** (moved to `archive/` directory):
- `app.py.old` - Original ChromaDB-based backend
- `app_chromadb.py` - ChromaDB implementation
- `app_milvus_backup.py` - Milvus backup implementation
- `Dockerfile.chromadb` - ChromaDB container configuration
- `requirements-chromadb.txt` - ChromaDB dependencies
- `deploy-chromadb.sh` / `deploy-chromadb.ps1` - ChromaDB deployment scripts
- `CHROMADB_MIGRATION.md` - Migration documentation
- `MIGRATION_FROM_CHROMADB.md` - Migration guide

### 2. Key Features

The consolidated OpenSearch backend includes:

✅ **Vector Search**: Hybrid search with BM25 and k-NN  
✅ **PDF Processing**: Simple PyPDF and advanced Docling pipelines  
✅ **URL Loading**: New `/api/load-pdf-url` endpoint for loading PDFs from URLs  
✅ **Web Scraping**: IBM Docs scraper for documentation ingestion  
✅ **Multiple Collections**: Support for different document collections  
✅ **Hierarchical Chunking**: Advanced document chunking with Docling  

### 3. API Endpoints

- `GET /health` - Health check
- `GET /api/collections` - List all collections
- `POST /api/search` - Search for relevant documents
- `POST /api/generate` - Generate LLM responses
- `POST /api/load-pdf` - Load PDF from local file
- `POST /api/load-pdf-url` - Load PDF from URL (new!)
- `POST /api/load-url` - Load content from web URL
- `POST /api/load-multiple-urls` - Batch load from multiple URLs

### 4. Deployment

**Current Deployment**:
- BuildConfig: `rag-backend-opensearch`
- Deployment: `rag-backend`
- Service: `rag-backend`
- Image: `rag-backend-opensearch:latest`

**Quick Deploy**:
```bash
cd rag-backend
./deploy.sh
```

Or manually:
```bash
oc start-build rag-backend-opensearch --from-dir=. --follow
```

### 5. Environment Variables

```bash
OPENSEARCH_HOST=opensearch-service
OPENSEARCH_PORT=9200
OPENSEARCH_USERNAME=admin
OPENSEARCH_PASSWORD=admin
OPENSEARCH_DB_PREFIX=rag
LLAMA_HOST=llama-service
LLAMA_PORT=8080
USE_DOCLING=false  # Set to true for advanced PDF processing
```

## Benefits of Consolidation

1. **Simplified Maintenance**: Single codebase to maintain
2. **Clearer Architecture**: No confusion about which backend is active
3. **Better Performance**: OpenSearch provides superior hybrid search
4. **Easier Deployment**: Single Dockerfile and deployment script
5. **Reduced Complexity**: Fewer dependencies and configuration options

## Migration Notes

If you need to reference the old ChromaDB or Milvus implementations, they are preserved in the `archive/` directory. However, the OpenSearch implementation is now the standard and recommended approach.

## Recent Enhancements

- **April 27, 2026**: Added `/api/load-pdf-url` endpoint for loading PDFs from URLs (supports Harry Potter demo in Part 2)
- Uses simple PyPDF approach for basic PDF loading
- Maintains compatibility with advanced Docling pipeline for complex documents

## Support

For issues or questions, refer to:
- `README.md` - General backend documentation
- `OPENSEARCH_QUICK_START.md` - OpenSearch setup guide
- `QUICK_DEPLOY.md` - Deployment instructions