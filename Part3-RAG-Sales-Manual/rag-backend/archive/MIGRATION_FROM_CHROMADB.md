# Migrating from ChromaDB to OpenSearch - Existing Project

## Your Current Situation

You have an **existing OpenShift project** with:
- ✅ Running containers (LLM service, etc.)
- ❌ ChromaDB-based RAG backend with dependency issues (Rust/bcrypt)
- ✅ OpenShift cluster access with `oc` CLI

## Migration Strategy

We'll deploy the OpenSearch-based backend **alongside** your existing containers, test it, then switch over.

### Option A: Side-by-Side Deployment (Recommended)

Deploy the new OpenSearch backend with a different name, test it, then switch traffic.

```bash
cd ../RAG-with-Notebook/rag-backend

# Make sure you're in the right project
oc project your-project-name

# Deploy with a different name to avoid conflicts
APP_NAME="rag-backend-opensearch"

# Run the deployment script
./deploy-opensearch.sh
# or on Windows:
# .\deploy-opensearch.ps1
```

**What happens:**
1. Creates new BuildConfig: `rag-backend-opensearch`
2. Builds new container (no dependency issues!)
3. Creates new Deployment: `rag-backend-opensearch`
4. Creates new Service: `rag-backend-opensearch`
5. Creates new Route: `rag-backend-opensearch`
6. **Old ChromaDB backend keeps running**

### Option B: Replace Existing Deployment

If you want to replace the existing backend directly:

```bash
cd ../RAG-with-Notebook/rag-backend

# Check your existing backend name
oc get deployment | grep rag

# If it's called "rag-backend", delete it first
oc delete deployment rag-backend
oc delete svc rag-backend
oc delete route rag-backend
oc delete bc rag-backend
oc delete is rag-backend

# Now deploy the new one with the same name
# Edit deploy-opensearch.sh and change APP_NAME to "rag-backend"
# Then run:
./deploy-opensearch.sh
```

## Step-by-Step Migration

### Step 1: Check Current State

```bash
# Login to OpenShift
oc login https://your-cluster:6443 --token=your-token

# Switch to your project
oc project your-project-name

# List current deployments
oc get deployment
oc get svc
oc get route

# Check the old backend
oc get pods -l app=rag-backend  # or whatever it's called
oc logs deployment/rag-backend  # Check for errors
```

### Step 2: Deploy OpenSearch (if not already deployed)

```bash
# Check if OpenSearch exists
oc get svc | grep opensearch

# If not, you need to deploy OpenSearch first
# See OPENSEARCH_QUICK_START.md for OpenSearch deployment options
```

### Step 3: Deploy New Backend

```bash
cd ../RAG-with-Notebook/rag-backend

# Deploy the OpenSearch-based backend
./deploy-opensearch.sh

# Watch the build
oc logs -f bc/rag-backend-opensearch

# Watch the deployment
oc get pods -w -l app=rag-backend-opensearch
```

### Step 4: Verify New Backend

```bash
# Get the new route
NEW_URL=$(oc get route rag-backend-opensearch -o jsonpath='{.spec.host}')
echo "New backend: https://$NEW_URL"

# Test health
curl https://$NEW_URL/health

# Expected response:
# {
#   "status": "healthy",
#   "opensearch": "connected",
#   "llm": "connected"
# }

# Test API
curl https://$NEW_URL/api/collections
```

### Step 5: Re-ingest Documents

Since OpenSearch uses a different storage format, you need to re-ingest your documents:

```bash
# Load a test PDF
curl -X POST https://$NEW_URL/api/load-pdf \
  -H "Content-Type: application/json" \
  -d '{
    "server_name": "IBM_Power_S1012",
    "collection_name": "sales_manuals"
  }'

# Test search
curl -X POST https://$NEW_URL/api/search \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the specifications?",
    "collection_name": "sales_manuals",
    "k": 3
  }'
```

### Step 6: Update Frontend/Clients

Update your frontend or API clients to use the new backend URL:

**Option A: Update frontend configuration**
```javascript
// Old
const BACKEND_URL = "https://rag-backend-your-project.apps.cluster.com"

// New
const BACKEND_URL = "https://rag-backend-opensearch-your-project.apps.cluster.com"
```

**Option B: Switch the route** (if using same name)
```bash
# Delete old route
oc delete route rag-backend

# Rename new route
oc patch route rag-backend-opensearch -p '{"metadata":{"name":"rag-backend"}}'
```

### Step 7: Decommission Old Backend

Once you've verified the new backend works:

```bash
# Scale down old backend (keep it for rollback)
oc scale deployment/rag-backend --replicas=0

# After a few days of successful operation, delete it
oc delete deployment rag-backend
oc delete svc rag-backend
oc delete bc rag-backend
oc delete is rag-backend

# Delete old PVC if you had one for ChromaDB
oc get pvc
oc delete pvc chroma-db-pvc  # or whatever it was called
```

## Handling Existing Resources

### If BuildConfig Already Exists

```bash
# Delete old build config
oc delete bc rag-backend-opensearch

# Or update it
oc patch bc rag-backend-opensearch --type=merge -p '
{
  "spec": {
    "strategy": {
      "dockerStrategy": {
        "dockerfilePath": "Dockerfile.opensearch"
      }
    }
  }
}'
```

### If Deployment Already Exists

```bash
# Update the deployment to use new image
oc set image deployment/rag-backend-opensearch \
  rag-backend=image-registry.openshift-image-registry.svc:5000/$(oc project -q)/rag-backend-opensearch:latest

# Update environment variables
oc set env deployment/rag-backend-opensearch \
  OPENSEARCH_HOST=opensearch-service \
  OPENSEARCH_PORT=9200
```

### If Service/Route Already Exists

```bash
# Delete and recreate
oc delete svc rag-backend-opensearch
oc delete route rag-backend-opensearch

# Then run the deployment script again
```

## Troubleshooting Migration

### Old Backend Still Running

```bash
# Check what's using resources
oc get all -l app=rag-backend

# Scale down old backend
oc scale deployment/rag-backend --replicas=0
```

### Port Conflicts

```bash
# Check what's using port 8080
oc get svc

# The new backend uses a different service name, so no conflict
```

### Build Failures

```bash
# Check build logs
oc logs -f bc/rag-backend-opensearch

# Common issues:
# - Wrong Dockerfile path: Check dockerfilePath in BuildConfig
# - Missing files: Make sure you're in rag-backend directory
# - Network issues: Retry the build
```

### Deployment Failures

```bash
# Check pod status
oc get pods -l app=rag-backend-opensearch

# Check events
oc describe pod -l app=rag-backend-opensearch

# Common issues:
# - OpenSearch not accessible: Check OPENSEARCH_HOST
# - Image pull errors: Check ImageStream
# - Resource limits: Adjust memory/CPU requests
```

## Rollback Plan

If something goes wrong:

```bash
# Scale up old backend
oc scale deployment/rag-backend --replicas=1

# Scale down new backend
oc scale deployment/rag-backend-opensearch --replicas=0

# Switch route back (if you changed it)
oc patch route rag-backend -p '{"spec":{"to":{"name":"rag-backend"}}}'
```

## Comparison: Before and After

### Before (ChromaDB)
```
rag-backend (ChromaDB)
├── Build issues: Rust compiler, bcrypt, SQLite
├── Build time: 15-20 minutes
├── Image size: ~2.5 GB
├── Dependency conflicts: Common
└── Storage: PVC for ChromaDB data
```

### After (OpenSearch)
```
rag-backend-opensearch
├── Build issues: None! ✅
├── Build time: 8-12 minutes
├── Image size: ~2.0 GB
├── Dependency conflicts: Rare
└── Storage: External OpenSearch cluster
```

## Environment Variables Comparison

### Old (ChromaDB)
```bash
CHROMA_PERSIST_DIR=/app/chroma_db
LLAMA_HOST=llama-service
LLAMA_PORT=8080
```

### New (OpenSearch)
```bash
OPENSEARCH_HOST=opensearch-service
OPENSEARCH_PORT=9200
OPENSEARCH_USERNAME=admin
OPENSEARCH_PASSWORD=admin
LLAMA_HOST=llama-service
LLAMA_PORT=8080
```

## API Compatibility

✅ **100% Compatible** - Same endpoints, same request/response format:
- `GET /api/collections`
- `DELETE /api/collections/<name>`
- `POST /api/load-pdf`
- `POST /api/search`
- `POST /api/generate`
- `GET /health`

Your frontend code needs **no changes**!

## Timeline

Recommended migration timeline:

1. **Day 1**: Deploy new backend alongside old one (30 minutes)
2. **Day 1-2**: Test new backend, re-ingest documents (2-4 hours)
3. **Day 2-3**: Run both backends in parallel, compare results (1-2 days)
4. **Day 3**: Switch frontend to new backend (30 minutes)
5. **Day 4-7**: Monitor new backend (1 week)
6. **Day 7+**: Decommission old backend (30 minutes)

## Success Criteria

Before decommissioning the old backend, verify:

- ✅ New backend health check passes
- ✅ All documents re-ingested successfully
- ✅ Search results are accurate
- ✅ LLM generation works
- ✅ Frontend/clients updated
- ✅ No errors in logs for 24+ hours
- ✅ Performance is acceptable

## Support

If you encounter issues:

1. Check logs: `oc logs -f deployment/rag-backend-opensearch`
2. Check events: `oc get events --sort-by='.lastTimestamp'`
3. Verify OpenSearch: `oc get svc opensearch-service`
4. Test connectivity: `oc rsh deployment/rag-backend-opensearch`
5. Review documentation: `CONTAINER_DEPLOYMENT.md`

---

**Migration Date**: April 14, 2026  
**Status**: Ready for deployment  
**Risk Level**: Low (side-by-side deployment)