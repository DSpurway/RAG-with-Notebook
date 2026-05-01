# Quick Deployment Guide - ChromaDB RAG Backend

## Prerequisites

✅ You must be in the `RAG-with-Notebook` directory
✅ You must be logged into OpenShift (`oc login`)
✅ LLM service must be deployed (llama-service)

## Deployment Steps

### Step 1: Create Persistent Storage

```bash
oc apply -f rag-backend/rag-backend-pvc.yaml
```

Expected output:
```
persistentvolumeclaim/rag-backend-storage created
```

### Step 2: Build the Image

```bash
cd rag-backend

# Create build config (first time only)
oc new-build --name rag-backend --binary --strategy docker

# Start the build
oc start-build rag-backend --from-dir=. --follow
```

Wait for build to complete (shows "Push successful").

### Step 3: Deploy the Backend

```bash
# Still in rag-backend directory
oc apply -f rag-backend-deploy.yaml
oc apply -f rag-backend-svc.yaml
oc apply -f rag-backend-route.yaml
```

### Step 4: Verify Deployment

```bash
# Check pod status
oc get pods -l app=rag-backend

# Watch logs
oc logs -f deployment/rag-backend

# Get the route URL
oc get route rag-backend -o jsonpath='{.spec.host}'
```

Look for these log messages:
```
✅ ChromaDB client initialized successfully
✅ Flask app started on port 8080
```

### Step 5: Test the Backend

```bash
# Get your route URL
ROUTE=$(oc get route rag-backend -o jsonpath='{.spec.host}')

# Test health endpoint
curl https://$ROUTE/health

# Expected response:
# {"status":"healthy","chromadb":"connected","llm":"connected"}

# List collections (should be empty initially)
curl https://$ROUTE/api/collections

# Expected response:
# {"success":true,"collections":[]}
```

## Troubleshooting

### Build Fails

```bash
# Check build logs
oc logs -f bc/rag-backend

# Common issues:
# - Network timeout: Retry the build
# - Missing files: Ensure you're in rag-backend directory
```

### Pod Not Starting

```bash
# Check pod status
oc describe pod -l app=rag-backend

# Check logs
oc logs -f deployment/rag-backend

# Common issues:
# - PVC not bound: Check PVC status with `oc get pvc`
# - Image pull error: Check build completed successfully
# - LLM service not found: Ensure llama-service is running
```

### Health Check Fails

```bash
# Check if LLM service is accessible
oc get svc llama-service

# Test LLM service directly
curl http://llama-service:8080/health

# If LLM service is down, RAG backend will show:
# {"status":"unhealthy","chromadb":"connected","llm":"disconnected"}
```

## Next Steps

Once deployed successfully:

1. **Load a PDF document:**
   ```bash
   curl -X POST https://$ROUTE/api/load-pdf \
     -H "Content-Type: application/json" \
     -d '{"server_name": "IBM_Power_S1014", "collection_name": "power_systems"}'
   ```

2. **Search documents:**
   ```bash
   curl -X POST https://$ROUTE/api/search \
     -H "Content-Type: application/json" \
     -d '{"question": "What are the specs?", "collection_name": "power_systems", "k": 3}'
   ```

3. **Update Carbon UI** to use the new backend URL

## Files Created

- ✅ `rag-backend-pvc.yaml` - Persistent storage (10Gi)
- ✅ `rag-backend-deploy.yaml` - Deployment with ChromaDB
- ✅ `rag-backend-svc.yaml` - Service definition
- ✅ `rag-backend-route.yaml` - OpenShift route
- ✅ `deploy-chromadb.sh` - Automated deployment script (Linux/Mac)

## Documentation

- [CHROMADB_MIGRATION.md](CHROMADB_MIGRATION.md) - Full migration details
- [README.md](README.md) - Complete API documentation
- [WEB_SCRAPING_FEATURE.md](WEB_SCRAPING_FEATURE.md) - Web scraping guide

## Support

If you encounter issues:
1. Check logs: `oc logs -f deployment/rag-backend`
2. Check pod events: `oc describe pod -l app=rag-backend`
3. Verify PVC: `oc get pvc rag-backend-storage`
4. Verify LLM service: `oc get svc llama-service`

# Made with Bob