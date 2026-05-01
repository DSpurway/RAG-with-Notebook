# OpenSearch RAG Backend - Container Deployment Guide

## Overview

This guide explains how to build and deploy the OpenSearch-based RAG backend as a container. The solution is **containerized** and runs in OpenShift/Kubernetes, not as a RHEL instance.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    OpenShift Cluster                     │
│                                                          │
│  ┌──────────────────┐      ┌──────────────────┐        │
│  │  RAG Backend     │      │   OpenSearch     │        │
│  │  Container       │─────▶│   Cluster        │        │
│  │  (app_opensearch)│      │   (separate)     │        │
│  └──────────────────┘      └──────────────────┘        │
│           │                                              │
│           ▼                                              │
│  ┌──────────────────┐                                   │
│  │  LLM Service     │                                   │
│  │  (llama-cpp)     │                                   │
│  └──────────────────┘                                   │
└─────────────────────────────────────────────────────────┘
```

## Container Build Process

### What Happens During Build

1. **Builder Stage** (UBI9 Python 3.12)
   - Installs gcc, gcc-c++, make, python-devel
   - Downloads IBM Power-optimized wheels (torch, sentence-transformers, etc.)
   - Installs opensearch-py and other dependencies
   - Copies application code

2. **Production Stage** (UBI9 Python 3.12)
   - Minimal runtime image
   - Only includes libgomp for OpenMP support
   - Copies Python packages from builder
   - Copies application code
   - Sets environment variables
   - Runs with gunicorn

### Key Differences from ChromaDB Build

| Aspect | ChromaDB Build | OpenSearch Build |
|--------|---------------|------------------|
| **Rust Compiler** | ✅ Required (for bcrypt) | ❌ Not needed |
| **Custom SQLite** | ✅ Build from source | ❌ Not needed |
| **Build Time** | ~15-20 minutes | ~8-12 minutes |
| **Image Size** | ~2.5 GB | ~2.0 GB |
| **Build Complexity** | High | Low |

## Deployment Methods

### Method 1: OpenShift Binary Build (Recommended)

This method builds the container **inside OpenShift** using the source code from your local directory.

```bash
cd ../RAG-with-Notebook/rag-backend

# Linux/Mac
./deploy-opensearch.sh

# Windows PowerShell
.\deploy-opensearch.ps1
```

**What the script does:**
1. Creates BuildConfig with Docker strategy
2. Creates ImageStream for the built image
3. Starts binary build from local directory
4. Creates Deployment with environment variables
5. Creates Service to expose the pod
6. Creates Route for external access

### Method 2: Manual OpenShift Build

```bash
# 1. Create build configuration
oc new-build --name=rag-backend-opensearch \
  --binary \
  --strategy=docker \
  --dockerfile=Dockerfile.opensearch

# 2. Start build from current directory
oc start-build rag-backend-opensearch --from-dir=. --follow

# 3. Create deployment
oc new-app rag-backend-opensearch \
  -e OPENSEARCH_HOST=opensearch-service \
  -e OPENSEARCH_PORT=9200 \
  -e OPENSEARCH_USERNAME=admin \
  -e OPENSEARCH_PASSWORD=admin \
  -e LLAMA_HOST=llama-service \
  -e LLAMA_PORT=8080

# 4. Expose service
oc expose svc/rag-backend-opensearch
```

### Method 3: Local Docker Build + Push

If you want to build locally and push to a registry:

```bash
# 1. Build locally
docker build -f Dockerfile.opensearch -t rag-backend-opensearch:latest .

# 2. Tag for your registry
docker tag rag-backend-opensearch:latest your-registry/rag-backend-opensearch:latest

# 3. Push to registry
docker push your-registry/rag-backend-opensearch:latest

# 4. Deploy in OpenShift
oc new-app your-registry/rag-backend-opensearch:latest \
  -e OPENSEARCH_HOST=opensearch-service \
  -e OPENSEARCH_PORT=9200
```

### Method 4: GitOps / Source-to-Image

```bash
# If your code is in a Git repository
oc new-app https://github.com/your-org/your-repo.git \
  --context-dir=RAG-with-Notebook/rag-backend \
  --strategy=docker \
  --dockerfile=Dockerfile.opensearch \
  --name=rag-backend-opensearch
```

## Container Configuration

### Environment Variables

The container is configured via environment variables (no config files needed):

```yaml
env:
  # OpenSearch Connection
  - name: OPENSEARCH_HOST
    value: "opensearch-service"
  - name: OPENSEARCH_PORT
    value: "9200"
  - name: OPENSEARCH_USERNAME
    value: "admin"
  - name: OPENSEARCH_PASSWORD
    value: "admin"
  
  # OpenSearch Configuration
  - name: OPENSEARCH_DB_PREFIX
    value: "rag"
  - name: OPENSEARCH_INDEX_NAME
    value: "default"
  - name: OPENSEARCH_NUM_SHARDS
    value: "1"
  
  # LLM Service
  - name: LLAMA_HOST
    value: "llama-service"
  - name: LLAMA_PORT
    value: "8080"
  
  # Application
  - name: PDF_DIR
    value: "/app/pdfs"
  - name: CORS_ORIGIN
    value: "*"
```

### Resource Requirements

```yaml
resources:
  requests:
    memory: "2Gi"    # Minimum for embeddings model
    cpu: "500m"      # 0.5 CPU cores
  limits:
    memory: "4Gi"    # Maximum allowed
    cpu: "2000m"     # 2 CPU cores
```

### Health Checks

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 60
  periodSeconds: 30
  timeoutSeconds: 10

readinessProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 30
  periodSeconds: 10
  timeoutSeconds: 5
```

## Verifying the Build

### Check Build Progress

```bash
# Watch build logs
oc logs -f bc/rag-backend-opensearch

# Check build status
oc get builds
```

### Check Deployment

```bash
# Check pod status
oc get pods -l app=rag-backend-opensearch

# View pod logs
oc logs -f deployment/rag-backend-opensearch

# Check events
oc get events --sort-by='.lastTimestamp'
```

### Test the Container

```bash
# Get the route URL
BACKEND_URL=$(oc get route rag-backend-opensearch -o jsonpath='{.spec.host}')

# Test health endpoint
curl https://$BACKEND_URL/health

# Expected response:
# {
#   "status": "healthy",
#   "opensearch": "connected",
#   "llm": "connected"
# }
```

## Rebuilding After Changes

### Rebuild from Local Changes

```bash
# Make your code changes, then:
oc start-build rag-backend-opensearch --from-dir=. --follow

# The deployment will automatically use the new image
```

### Force Rollout

```bash
# If the deployment doesn't pick up the new image:
oc rollout restart deployment/rag-backend-opensearch

# Watch the rollout
oc rollout status deployment/rag-backend-opensearch
```

## Container Logs

### View Real-time Logs

```bash
# Follow logs from all pods
oc logs -f deployment/rag-backend-opensearch

# View logs from specific pod
oc logs -f pod/rag-backend-opensearch-xxxxx
```

### Debug Container Issues

```bash
# Get shell access to running container
oc rsh deployment/rag-backend-opensearch

# Inside container, check:
python --version                    # Python 3.12
pip list | grep opensearch          # opensearch-py installed
env | grep OPENSEARCH              # Environment variables
curl http://opensearch-service:9200 # OpenSearch connectivity
```

## Scaling the Container

### Horizontal Scaling

```bash
# Scale to multiple replicas
oc scale deployment/rag-backend-opensearch --replicas=3

# Auto-scaling based on CPU
oc autoscale deployment/rag-backend-opensearch \
  --min=2 --max=5 --cpu-percent=70
```

### Vertical Scaling

```bash
# Update resource limits
oc set resources deployment/rag-backend-opensearch \
  --requests=cpu=1,memory=4Gi \
  --limits=cpu=2,memory=8Gi
```

## Container Security

### Running as Non-Root

The container runs as a non-root user by default (inherited from UBI9 Python base image).

### Security Context

```yaml
securityContext:
  runAsNonRoot: true
  allowPrivilegeEscalation: false
  capabilities:
    drop:
      - ALL
```

## Troubleshooting Container Issues

### Build Failures

```bash
# Check build logs
oc logs -f bc/rag-backend-opensearch

# Common issues:
# - Network timeout downloading wheels
# - Insufficient resources for build
# - Missing dependencies in requirements file
```

### Runtime Failures

```bash
# Check pod status
oc describe pod -l app=rag-backend-opensearch

# Common issues:
# - OpenSearch not accessible
# - Insufficient memory (OOMKilled)
# - Environment variables not set
# - LLM service not available
```

### Connection Issues

```bash
# Test OpenSearch from container
oc rsh deployment/rag-backend-opensearch
curl -k https://opensearch-service:9200

# Test LLM service
curl http://llama-service:8080/health
```

## Container Updates

### Update Application Code

1. Modify `app_opensearch.py`
2. Rebuild: `oc start-build rag-backend-opensearch --from-dir=. --follow`
3. Verify: Check logs and test endpoints

### Update Dependencies

1. Modify `requirements-opensearch.txt`
2. Rebuild container (dependencies installed during build)
3. Test thoroughly

### Update Base Image

The Dockerfile uses `registry.access.redhat.com/ubi9/python-312:latest`. To update:

```bash
# Pull latest base image
oc import-image ubi9/python-312:latest --from=registry.access.redhat.com/ubi9/python-312:latest --confirm

# Rebuild
oc start-build rag-backend-opensearch --from-dir=. --follow
```

## Production Considerations

### High Availability

```yaml
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
```

### Persistent Storage (Optional)

If you need to persist downloaded models:

```yaml
volumeMounts:
  - name: models-cache
    mountPath: /root/.cache/huggingface
volumes:
  - name: models-cache
    persistentVolumeClaim:
      claimName: models-cache-pvc
```

### Monitoring

```bash
# Prometheus metrics (if enabled)
curl https://$BACKEND_URL/metrics

# Resource usage
oc adm top pods -l app=rag-backend-opensearch
```

## Summary

✅ **Container-based deployment** - Not a RHEL instance  
✅ **Built in OpenShift** - Using binary build from local directory  
✅ **Simplified build** - No Rust, no custom SQLite  
✅ **Production-ready** - Health checks, resource limits, scaling  
✅ **Easy updates** - Rebuild and redeploy with one command  

The entire solution is containerized and designed to run in OpenShift/Kubernetes environments!