# Dual Model LLM Implementation Summary

## Overview

Enhanced the RAG demo's LLM deployment to support **both TinyLlama and Granite 4.0** models in a single container, with easy switching between them via environment variable.

**Date**: April 13, 2026  
**Location**: `Part1-Deploy-LLM/` directory

## Problem Statement

The original RAG demo had a progression issue:
- **Part 1**: Used TinyLlama for basic LLM demonstrations
- **Part 2/3**: Jumped to using Granite models for RAG with complex documents
- **Issue**: Required separate container builds or manual model swapping

The README instructed users to deploy from `Part3-RAG-Sales-Manual/llama-cpp-server`, which only had Granite, making it confusing for Part 1 demonstrations.

## Solution

Created a flexible LLM server container that:
1. **Includes both models** at build time
2. **Starts with TinyLlama** by default (Part 1)
3. **Switches to Granite** via environment variable (Part 2/3)
4. **No rebuild required** to change models

## Architecture

```
┌─────────────────────────────────────────────┐
│   llama-service Container                   │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │  llama.cpp Server (compiled)        │   │
│  │  - OpenBLAS acceleration            │   │
│  │  - Power10 MMA support              │   │
│  └──────────────┬──────────────────────┘   │
│                 │                           │
│  ┌──────────────▼──────────────────────┐   │
│  │  /start-llama.sh                    │   │
│  │  - Reads LLM_MODEL env var          │   │
│  │  - Selects model file               │   │
│  │  - Starts llama-server              │   │
│  └──────────────┬──────────────────────┘   │
│                 │                           │
│         ┌───────┴────────┐                 │
│         │                │                 │
│  ┌──────▼──────┐  ┌─────▼──────┐          │
│  │ TinyLlama   │  │  Granite   │          │
│  │ 1.1B Q8_0   │  │  4.0 Micro │          │
│  │ ~1.1GB      │  │  ~2.5GB    │          │
│  └─────────────┘  └────────────┘          │
│                                             │
│  Total Size: ~3.6GB + base image           │
└─────────────────────────────────────────────┘
```

## Files Created/Modified

### 1. `Part1-Deploy-LLM/Dockerfile` (NEW)
**99 lines** - Multi-stage Docker build with:
- Both TinyLlama and Granite 4.0 models downloaded
- Embedded startup script for model selection
- OpenBLAS and llama.cpp compilation
- Power10 optimization

Key features:
```dockerfile
# Downloads both models
RUN wget https://huggingface.co/.../tinyllama-1.1b-chat-v1.0.Q8_0.gguf
RUN wget https://huggingface.co/.../granite-4.0-micro-Q4_K_M.gguf

# Startup script with model selection
ENTRYPOINT ["/start-llama.sh"]
```

### 2. `Part1-Deploy-LLM/llama-deploy.yaml` (MODIFIED)
**65 lines** - Updated Kubernetes deployment:
- Removed init container (models now in image)
- Added `LLM_MODEL` environment variable
- Simplified configuration
- Better resource limits

Key changes:
```yaml
env:
  - name: LLM_MODEL
    value: "tinyllama"  # or "granite"
```

### 3. `Part1-Deploy-LLM/README.md` (NEW)
**258 lines** - Comprehensive documentation:
- Quick start guide
- Model switching instructions
- Resource requirements
- Troubleshooting guide
- Integration with RAG backend

### 4. `Part1-Deploy-LLM/deploy.sh` (NEW)
**107 lines** - Automated deployment script:
- Interactive model selection
- Build and deploy automation
- Status checking
- User-friendly output

## Model Details

### TinyLlama 1.1B Chat v1.0 (Q8_0)
- **Use Case**: Part 1 - Basic LLM demonstrations
- **Size**: ~1.1GB
- **Parameters**: 1.1 billion
- **Quantization**: Q8_0 (8-bit, high quality)
- **Best For**: 
  - Quick responses
  - General conversation
  - Demonstrating hallucinations
  - Lower resource usage

### Granite 4.0 Micro (Q4_K_M)
- **Use Case**: Part 2/3 - RAG with complex documents
- **Size**: ~2.5GB
- **Parameters**: ~4 billion
- **Quantization**: Q4_K_M (4-bit, balanced)
- **Best For**:
  - Technical documentation
  - Sales manual analysis
  - More accurate responses
  - Complex reasoning

## Usage Examples

### Deploy with TinyLlama (Default)
```bash
cd Part1-Deploy-LLM
./deploy.sh
# Select option 1 for TinyLlama
```

### Switch to Granite for RAG
```bash
oc set env deployment/llama-service LLM_MODEL=granite
```

### Switch back to TinyLlama
```bash
oc set env deployment/llama-service LLM_MODEL=tinyllama
```

### Verify current model
```bash
oc logs deployment/llama-service | grep "Starting with"
```

## Startup Script Logic

The embedded `/start-llama.sh` script:

```bash
MODEL_NAME=${LLM_MODEL:-tinyllama}  # Default to tinyllama

case "$MODEL_NAME" in
  tinyllama)
    MODEL_PATH="/models/tinyllama-1.1b-chat-v1.0.Q8_0.gguf"
    ;;
  granite)
    MODEL_PATH="/models/granite-4.0-micro-Q4_K_M.gguf"
    ;;
esac

exec /llama.cpp/build/bin/llama-server -m "$MODEL_PATH" ...
```

## Benefits

### 1. **Simplified Workflow**
- Single container for entire demo
- No need to rebuild for different parts
- Clear progression from Part 1 to Part 2/3

### 2. **Resource Efficiency**
- Models downloaded once at build time
- No runtime downloads
- Faster pod startup

### 3. **Flexibility**
- Easy switching between models
- Can run both models in different namespaces
- Environment-based configuration

### 4. **Better Demo Flow**
- Start with simple TinyLlama (Part 1)
- Show limitations and hallucinations
- Switch to Granite for RAG (Part 2/3)
- Demonstrate improvement with RAG

## Resource Requirements

### Minimum
- **CPU**: 2 cores (Power10 with MMA)
- **Memory**: 4GB
- **Storage**: 5GB

### Recommended
- **CPU**: 4 cores
- **Memory**: 8GB (allows comfortable switching)
- **Storage**: 10GB

## Integration with RAG Backend

The RAG backend (from `rag-backend/`) connects to this service:

```yaml
# RAG backend configuration
env:
  - name: LLAMA_HOST
    value: "llama-service"
  - name: LLAMA_PORT
    value: "8080"
```

**Recommended workflow:**
1. Deploy llama-service with TinyLlama (Part 1)
2. Demonstrate basic LLM capabilities
3. Deploy Milvus vector database (Part 2)
4. Switch llama-service to Granite
5. Deploy RAG backend (Part 3)
6. Demonstrate RAG improvements

## Deployment Steps

### Option 1: Using the deployment script
```bash
cd Part1-Deploy-LLM
chmod +x deploy.sh  # On Linux/Mac
./deploy.sh
```

### Option 2: Manual deployment
```bash
# Build the image
oc new-build --name llama-service --binary --strategy docker
oc start-build llama-service --from-dir=. --follow

# Deploy
oc apply -f llama-deploy.yaml
oc apply -f llama-svc.yaml
oc apply -f llama-route.yaml
```

## Testing

### Health check
```bash
curl http://llama-service:8080/health
```

### Test inference
```bash
curl http://llama-service:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Hello!"}],
    "temperature": 0.7
  }'
```

## Troubleshooting

### Check which model is running
```bash
oc logs deployment/llama-service | grep "Starting with"
```

### Model not loading
```bash
# Verify models exist
oc exec deployment/llama-service -- ls -lh /models/
```

### Out of memory
- Increase memory limits in deployment
- Use TinyLlama instead of Granite

## Future Enhancements

Potential improvements:
1. **Add more models**: Granite 3.0, Llama 2, etc.
2. **Hot-swapping**: Switch models without pod restart
3. **Model caching**: Share models across multiple pods
4. **Auto-selection**: Choose model based on query complexity
5. **Metrics**: Track which model is used for analytics

## Comparison with Previous Approach

### Before
- Separate containers for different models
- Manual model downloads in init containers
- Confusing deployment paths
- Rebuild required to change models

### After
- Single container with both models
- Models baked into image
- Clear deployment path
- Environment variable switching

## Documentation Updates Needed

The main `README.md` should be updated to:
1. Reference the new `Part1-Deploy-LLM/` directory
2. Explain the dual-model approach
3. Update deployment instructions
4. Show model switching examples

## Conclusion

This implementation provides a flexible, efficient, and user-friendly way to progress through the RAG demo:

- **Part 1**: Start with TinyLlama for basic demonstrations
- **Part 2**: Deploy Milvus and prepare for RAG
- **Part 3**: Switch to Granite and deploy RAG backend

The solution maintains backward compatibility while significantly improving the demo experience and reducing deployment complexity.

## Files Summary

| File | Lines | Purpose |
|------|-------|---------|
| `Dockerfile` | 99 | Multi-model container build |
| `llama-deploy.yaml` | 65 | Kubernetes deployment |
| `README.md` | 258 | Complete documentation |
| `deploy.sh` | 107 | Automated deployment |
| `DUAL_MODEL_IMPLEMENTATION.md` | This file | Implementation summary |

**Total**: 529+ lines of new/modified code and documentation