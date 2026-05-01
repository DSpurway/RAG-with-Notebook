# OpenSearch RAG Backend - Quick Start Guide

## Overview

This guide helps you quickly deploy the RAG backend with OpenSearch support, eliminating the dependency issues encountered with ChromaDB.

## Prerequisites

1. **OpenShift/Kubernetes cluster** with access
2. **OpenSearch cluster** deployed and accessible
3. **oc CLI** installed and logged in
4. **LLM service** (llama-service) deployed

## Key Benefits Over ChromaDB

✅ **No Rust compiler needed** - Eliminates bcrypt build issues  
✅ **No custom SQLite** - Uses standard libraries  
✅ **Better scalability** - Enterprise-grade distributed search  
✅ **Advanced search** - Hybrid semantic + keyword search  
✅ **Proven solution** - Based on IBM project-ai-services  

## Quick Deployment

### Option 1: Using Deployment Script (Recommended)

**Linux/Mac:**
```bash
cd ../RAG-with-Notebook/rag-backend
chmod +x deploy-opensearch.sh
./deploy-opensearch.sh
```

**Windows (PowerShell):**
```powershell
cd ..\RAG-with-Notebook\rag-backend
.\deploy-opensearch.ps1
```

### Option 2: Manual Deployment

```bash
# 1. Build the image
oc new-build --name=rag-backend-opensearch \
  --binary \
  --strategy=docker \
  --dockerfile=Dockerfile.opensearch

oc start-build rag-backend-opensearch --from-dir=. --follow

# 2. Deploy the application
oc new-app rag-backend-opensearch

# 3. Set environment variables
oc set env deployment/rag-backend-opensearch \
  OPENSEARCH_HOST=opensearch-service \
  OPENSEARCH_PORT=9200 \
  OPENSEARCH_USERNAME=admin \
  OPENSEARCH_PASSWORD=admin \
  LLAMA_HOST=llama-service \
  LLAMA_PORT=8080

# 4. Expose the service
oc expose svc/rag-backend-opensearch
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENSEARCH_HOST` | opensearch-service | OpenSearch hostname |
| `OPENSEARCH_PORT` | 9200 | OpenSearch port |
| `OPENSEARCH_USERNAME` | admin | OpenSearch username |
| `OPENSEARCH_PASSWORD` | admin | OpenSearch password |
| `OPENSEARCH_DB_PREFIX` | rag | Index name prefix |
| `OPENSEARCH_INDEX_NAME` | default | Default index name |
| `OPENSEARCH_NUM_SHARDS` | 1 | Number of shards |
| `LLAMA_HOST` | llama-service | LLM service hostname |
| `LLAMA_PORT` | 8080 | LLM service port |
| `PDF_DIR` | /app/pdfs | PDF storage directory |
| `CORS_ORIGIN` | * | CORS allowed origins |

### Update Configuration

```bash
oc set env deployment/rag-backend-opensearch \
  OPENSEARCH_HOST=my-opensearch-cluster \
  OPENSEARCH_PASSWORD=my-secure-password
```

## Testing

### 1. Health Check

```bash
BACKEND_URL=$(oc get route rag-backend-opensearch -o jsonpath='{.spec.host}')
curl https://$BACKEND_URL/health
```

Expected response:
```json
{
  "status": "healthy",
  "opensearch": "connected",
  "llm": "connected"
}
```

### 2. List Collections

```bash
curl https://$BACKEND_URL/api/collections
```

### 3. Load a PDF

```bash
curl -X POST https://$BACKEND_URL/api/load-pdf \
  -H "Content-Type: application/json" \
  -d '{
    "server_name": "IBM_Power_S1012",
    "collection_name": "sales_manuals"
  }'
```

### 4. Search Documents

```bash
curl -X POST https://$BACKEND_URL/api/search \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the specifications?",
    "collection_name": "sales_manuals",
    "k": 3,
    "mode": "hybrid"
  }'
```

Search modes:
- `dense` - Pure semantic search (k-NN)
- `sparse` - Keyword search (BM25)
- `hybrid` - Combined semantic + keyword (default)

### 5. Generate Response

```bash
curl -X POST https://$BACKEND_URL/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Based on the context, answer: What are the key features?",
    "temperature": 0.1,
    "n_predict": 200
  }'
```

## Deploying OpenSearch

If you don't have OpenSearch deployed yet:

### Option 1: Simple Docker Compose (Development)

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

### Option 2: OpenShift Deployment

```bash
# Deploy OpenSearch using the official operator or Helm chart
# See: https://opensearch.org/docs/latest/install-and-configure/install-opensearch/helm/
```

## Troubleshooting

### OpenSearch Connection Issues

```bash
# Check if OpenSearch is accessible
oc get svc opensearch-service

# Test connection from within the cluster
oc run -it --rm debug --image=curlimages/curl --restart=Never -- \
  curl -k https://opensearch-service:9200
```

### Backend Pod Issues

```bash
# Check pod status
oc get pods -l app=rag-backend-opensearch

# View logs
oc logs -f deployment/rag-backend-opensearch

# Describe pod for events
oc describe pod -l app=rag-backend-opensearch
```

### Build Issues

```bash
# Check build logs
oc logs -f bc/rag-backend-opensearch

# Rebuild
oc start-build rag-backend-opensearch --from-dir=. --follow
```

## Monitoring

### Check Resource Usage

```bash
oc adm top pods -l app=rag-backend-opensearch
```

### View Metrics

```bash
# Get pod metrics
oc get --raw /apis/metrics.k8s.io/v1beta1/namespaces/$(oc project -q)/pods
```

## Scaling

### Horizontal Scaling

```bash
# Scale to 3 replicas
oc scale deployment/rag-backend-opensearch --replicas=3
```

### Vertical Scaling

```bash
# Update resource limits
oc set resources deployment/rag-backend-opensearch \
  --requests=cpu=1,memory=4Gi \
  --limits=cpu=2,memory=8Gi
```

## Migration from ChromaDB

If you're migrating from the ChromaDB version:

1. **Deploy OpenSearch** (see above)
2. **Deploy new backend** using this guide
3. **Re-ingest documents** using `/api/load-pdf` endpoint
4. **Update frontend** to point to new backend URL
5. **Test thoroughly** before decommissioning old backend
6. **Remove old ChromaDB** deployment when satisfied

## API Compatibility

The OpenSearch backend maintains **100% API compatibility** with the ChromaDB version:

- Same endpoints
- Same request/response formats
- Same error handling
- Drop-in replacement

Only internal implementation changed - your frontend code needs no modifications!

## Performance Tips

1. **Adjust shards**: Set `OPENSEARCH_NUM_SHARDS` based on cluster size
2. **Use hybrid search**: Best balance of accuracy and relevance
3. **Tune k-NN**: Adjust `ef_search` in index settings for speed vs accuracy
4. **Monitor memory**: Embeddings model needs ~2GB RAM
5. **Scale horizontally**: Add replicas for high traffic

## Support

For issues:
1. Check logs: `oc logs -f deployment/rag-backend-opensearch`
2. Verify OpenSearch: Test connection and cluster health
3. Review environment variables: `oc set env deployment/rag-backend-opensearch --list`
4. Check the main migration guide: `OPENSEARCH_MIGRATION.md`

## Next Steps

- [ ] Deploy OpenSearch cluster
- [ ] Deploy RAG backend
- [ ] Test health endpoint
- [ ] Load sample PDFs
- [ ] Test search functionality
- [ ] Update frontend configuration
- [ ] Monitor performance
- [ ] Scale as needed

---

**Version**: 3.0.0  
**Based on**: IBM project-ai-services rag-base  
**Date**: April 14, 2026