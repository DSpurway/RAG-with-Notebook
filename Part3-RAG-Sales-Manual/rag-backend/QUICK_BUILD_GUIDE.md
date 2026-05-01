# Quick Build & Deploy Guide - RAG Backend with ChromaDB

## Prerequisites

- OpenShift CLI (`oc`) installed and logged in
- Access to Power10 OpenShift cluster
- PowerShell (Windows) or Bash (Linux/Mac)

## Quick Deploy (Automated)

### Windows PowerShell
```powershell
cd ..\RAG-with-Notebook
.\rag-backend\deploy-chromadb.ps1
```

### Linux/Mac Bash
```bash
cd ../RAG-with-Notebook
./rag-backend/deploy-chromadb.sh
```

This automated script will:
1. ✅ Create PVC for data persistence
2. ✅ Build the Docker image on OpenShift
3. ✅ Deploy the backend service
4. ✅ Create route and expose the service
5. ✅ Wait for deployment to be ready
6. ✅ Display the service URL

## Manual Build Steps

If you prefer manual control:

### 1. Create Storage
```bash
cd RAG-with-Notebook/rag-backend
oc apply -f rag-backend-pvc.yaml
```

### 2. Create Build Config (first time only)
```bash
oc new-build --name rag-backend --binary --strategy docker
```

### 3. Start Build
```bash
oc start-build rag-backend --from-dir=. --follow
```

**Note**: The build will:
- Install Rust compiler for bcrypt compilation
- Use IBM Power-optimized wheels for torch, openblas, sentence-transformers
- Install ChromaDB and all dependencies
- Take ~5-10 minutes on first build

### 4. Deploy
```bash
oc apply -f rag-backend-deploy.yaml
oc apply -f rag-backend-svc.yaml
oc apply -f rag-backend-route.yaml
```

### 5. Wait for Ready
```bash
oc rollout status deployment/rag-backend --timeout=5m
```

### 6. Get Service URL
```bash
oc get route rag-backend -o jsonpath='{.spec.host}'
```

## Verify Deployment

### Check Pod Status
```bash
oc get pods -l app=rag-backend
```

Expected output:
```
NAME                           READY   STATUS    RESTARTS   AGE
rag-backend-xxxxxxxxxx-xxxxx   1/1     Running   0          2m
```

### Check Logs
```bash
oc logs -f deployment/rag-backend
```

Look for:
```
INFO:__main__:Web scraping module not available. Running in PDF-only mode.
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:8080
```

### Test Health Endpoint
```bash
# Get the route URL
$ROUTE = oc get route rag-backend -o jsonpath='{.spec.host}'

# Test health
curl https://$ROUTE/health
```

Expected response:
```json
{
  "status": "healthy",
  "chromadb": "connected",
  "llm": "connected"
}
```

### Test Collections Endpoint
```bash
curl https://$ROUTE/api/collections
```

Expected response (empty initially):
```json
{
  "collections": []
}
```

## Troubleshooting

### Build Fails with "Rust compiler not found"
**Solution**: The Dockerfile has been updated to include Rust. Rebuild:
```bash
oc start-build rag-backend --from-dir=. --follow
```

### Pod CrashLoopBackOff
**Check logs**:
```bash
oc logs deployment/rag-backend
```

Common issues:
- Missing PVC: `oc get pvc rag-backend-storage`
- Wrong permissions: Check pod security context
- Missing dependencies: Rebuild image

### "chromadb module not found"
**Solution**: Image wasn't rebuilt after Dockerfile changes
```bash
oc start-build rag-backend --from-dir=. --follow
oc rollout restart deployment/rag-backend
```

### Slow Build Times
**Expected**: First build takes 5-10 minutes due to:
- Compiling bcrypt with Rust
- Downloading ML models
- Building sentence-transformers

Subsequent builds are faster (~2-3 minutes) due to layer caching.

### Route Not Accessible
**Check route**:
```bash
oc get route rag-backend
```

**Check service**:
```bash
oc get svc rag-backend
```

**Check endpoints**:
```bash
oc get endpoints rag-backend
```

## Update Existing Deployment

If you've already deployed and need to update:

### Update Code Only
```bash
cd RAG-with-Notebook/rag-backend
oc start-build rag-backend --from-dir=. --follow
# Deployment will auto-update with new image
```

### Update Deployment Config
```bash
oc apply -f rag-backend-deploy.yaml
oc rollout restart deployment/rag-backend
```

### Force Rebuild
```bash
oc delete bc/rag-backend
oc new-build --name rag-backend --binary --strategy docker
oc start-build rag-backend --from-dir=. --follow
```

## Clean Up

### Delete Everything
```bash
oc delete deployment/rag-backend
oc delete svc/rag-backend
oc delete route/rag-backend
oc delete pvc/rag-backend-storage
oc delete bc/rag-backend
oc delete is/rag-backend
```

### Keep Data, Remove Service
```bash
oc delete deployment/rag-backend
oc delete svc/rag-backend
oc delete route/rag-backend
# PVC remains for data persistence
```

## Next Steps

After successful deployment:

1. **Load PDFs**: Use the `/api/load-pdf` endpoint
2. **Create Collections**: Organize documents by topic
3. **Test Search**: Query your documents
4. **Integrate with UI**: Update Carbon UI to use the new backend

## Support Files

- `Dockerfile` - Multi-stage build with Rust support
- `requirements.txt` - Python dependencies including ChromaDB
- `app.py` - Flask application with ChromaDB integration
- `DEPENDENCY_FIX.md` - Details on the Rust/bcrypt fix
- `CHROMADB_MIGRATION.md` - Full migration documentation

## Performance Notes

- **Build Time**: 5-10 minutes (first), 2-3 minutes (subsequent)
- **Startup Time**: ~30 seconds
- **Memory Usage**: 2-4GB
- **Storage**: PVC size defined in `rag-backend-pvc.yaml` (default: 10Gi)

## Key Changes from Milvus

- ✅ Single service (no etcd, MinIO, Milvus)
- ✅ Embedded database (ChromaDB)
- ✅ Persistent storage via PVC
- ✅ Same API endpoints (backward compatible)
- ✅ Better Power10 support
- ✅ Faster deployment