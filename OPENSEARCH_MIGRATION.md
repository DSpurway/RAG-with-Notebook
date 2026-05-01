# OpenSearch Migration Guide

## Overview

This document describes the migration from ChromaDB to OpenSearch for the RAG backend, based on the IBM project-ai-services implementation.

## Key Differences

### ChromaDB vs OpenSearch

| Feature | ChromaDB | OpenSearch |
|---------|----------|------------|
| **Type** | Embedded vector database | Distributed search engine with vector support |
| **Deployment** | In-process or client-server | Requires separate OpenSearch cluster |
| **Dependencies** | chromadb, chroma-hnswlib | opensearch-py |
| **Scalability** | Limited | Enterprise-grade horizontal scaling |
| **Search Modes** | Similarity search only | Dense (k-NN), Sparse (BM25), Hybrid |
| **Dependency Issues** | Rust compiler needed for bcrypt | Cleaner dependency tree |

### Benefits of OpenSearch

1. **No Rust Compiler Required**: Eliminates the bcrypt/Rust dependency issue
2. **Better Scalability**: Production-ready distributed architecture
3. **Advanced Search**: Hybrid search combining semantic + keyword matching
4. **IBM Support**: Proven implementation in IBM project-ai-services
5. **Cleaner Dependencies**: Fewer build-time complications on ppc64le

## Architecture Changes

### Current (ChromaDB)
```
Flask App → ChromaDB (embedded) → Persistent Volume
```

### New (OpenSearch)
```
Flask App → OpenSearch Client → OpenSearch Cluster (separate service)
```

## Environment Variables

### Required for OpenSearch

```bash
# OpenSearch Connection
OPENSEARCH_HOST=opensearch-service
OPENSEARCH_PORT=9200
OPENSEARCH_USERNAME=admin
OPENSEARCH_PASSWORD=admin

# Index Configuration
OPENSEARCH_DB_PREFIX=rag
OPENSEARCH_INDEX_NAME=default
OPENSEARCH_NUM_SHARDS=1

# LLM Configuration (unchanged)
LLAMA_HOST=llama-service
LLAMA_PORT=8080
```

## Dependency Changes

### Removed Dependencies
- `chromadb>=0.5.23` - No longer needed
- `rust` and `cargo` - Build dependencies removed
- `chroma-hnswlib` - ChromaDB-specific

### Added Dependencies
- `opensearch-py==3.0.0` - OpenSearch Python client

### Unchanged Dependencies
- `sentence-transformers>=3.0.0` - Still used for embeddings
- `transformers>=4.41.0` - Still needed
- `langchain` packages - Still used for document processing
- `pypdf` - Still used for PDF loading

## API Changes

### Endpoints (Unchanged)
All existing endpoints remain the same:
- `GET /api/collections` - List collections (now lists OpenSearch indices)
- `DELETE /api/collections/<name>` - Drop collection
- `POST /api/load-pdf` - Load PDF
- `POST /api/load-url` - Load URL (if web scraping enabled)
- `POST /api/search` - Search documents
- `POST /api/generate` - Generate LLM response
- `GET /health` - Health check

### Internal Changes
- Collections → OpenSearch indices
- ChromaDB client → OpenSearch client
- Similarity search → Configurable search modes (dense/sparse/hybrid)

## Search Modes

OpenSearch supports three search modes:

1. **Dense (Semantic)**: Pure vector similarity using k-NN
2. **Sparse (Keyword)**: BM25 full-text search
3. **Hybrid (Default)**: Combines dense + sparse with score fusion

## Deployment Requirements

### OpenSearch Cluster

You'll need to deploy an OpenSearch cluster separately. Options:

1. **OpenShift/Kubernetes**: Use OpenSearch Operator
2. **Docker Compose**: Use official OpenSearch images
3. **Managed Service**: AWS OpenSearch Service, etc.

### Minimal OpenSearch Setup (Docker Compose)

```yaml
version: '3'
services:
  opensearch:
    image: opensearchproject/opensearch:2.11.0
    environment:
      - discovery.type=single-node
      - OPENSEARCH_JAVA_OPTS=-Xms512m -Xmx512m
      - DISABLE_SECURITY_PLUGIN=true
    ports:
      - "9200:9200"
    volumes:
      - opensearch-data:/usr/share/opensearch/data

volumes:
  opensearch-data:
```

## Migration Steps

### 1. Update Dependencies

```bash
cd ../RAG-with-Notebook/rag-backend
# Use the new requirements-opensearch.txt
pip install -r requirements-opensearch.txt
```

### 2. Deploy OpenSearch

Deploy OpenSearch cluster (see deployment options above)

### 3. Update Environment Variables

Set the OpenSearch connection variables in your deployment

### 4. Deploy Updated Backend

```bash
# Build new image
docker build -t rag-backend:opensearch -f Dockerfile.opensearch .

# Or use OpenShift build
oc start-build rag-backend --from-dir=. --follow
```

### 5. Migrate Data (Optional)

If you have existing data in ChromaDB:
1. Export documents from ChromaDB
2. Re-ingest using the new `/api/load-pdf` endpoint
3. OpenSearch will create new indices automatically

## Testing

### 1. Health Check
```bash
curl http://rag-backend:8080/health
```

Expected response:
```json
{
  "status": "healthy",
  "opensearch": "connected",
  "llm": "connected"
}
```

### 2. Load PDF
```bash
curl -X POST http://rag-backend:8080/api/load-pdf \
  -H "Content-Type: application/json" \
  -d '{"server_name": "IBM_Power_S1012", "collection_name": "sales_manuals"}'
```

### 3. Search
```bash
curl -X POST http://rag-backend:8080/api/search \
  -H "Content-Type: application/json" \
  -d '{"question": "What are the specifications?", "collection_name": "sales_manuals", "k": 3}'
```

## Performance Considerations

### OpenSearch Tuning

1. **Shards**: Set `OPENSEARCH_NUM_SHARDS` based on cluster size
2. **Replicas**: Configure auto-expansion for high availability
3. **Heap Size**: Allocate 50% of available RAM to OpenSearch JVM
4. **k-NN Settings**: Adjust `ef_search` for accuracy vs speed tradeoff

### Embedding Model

The embedding model (all-MiniLM-L6-v2) remains the same:
- Dimension: 384
- Fast inference
- Good balance of quality and speed

## Rollback Plan

If issues occur:

1. Keep old ChromaDB deployment running
2. Switch traffic back to ChromaDB service
3. Investigate OpenSearch issues
4. Re-attempt migration when resolved

## Files Modified

- `requirements-opensearch.txt` - New dependencies
- `app_opensearch.py` - New backend implementation
- `Dockerfile.opensearch` - Updated Dockerfile
- `rag-backend-opensearch-deploy.yaml` - OpenShift deployment

## References

- [IBM project-ai-services](https://github.com/IBM/project-ai-services/tree/main/images/rag-base)
- [OpenSearch Documentation](https://opensearch.org/docs/latest/)
- [opensearch-py Client](https://github.com/opensearch-project/opensearch-py)
- [OpenSearch k-NN Plugin](https://opensearch.org/docs/latest/search-plugins/knn/index/)

## Support

For issues or questions:
1. Check OpenSearch cluster health
2. Review backend logs
3. Verify environment variables
4. Test OpenSearch connectivity directly

---

**Migration Date**: April 14, 2026  
**Based on**: IBM project-ai-services rag-base implementation  
**Status**: Ready for testing