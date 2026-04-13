# Part 1: Deploy LLM with Dual Model Support

This deployment provides a flexible LLM server that includes **both** TinyLlama and Granite 4.0 models, allowing you to switch between them based on your use case.

## Overview

The container includes:
- **TinyLlama 1.1B** (Q8_0) - Lightweight model for Part 1 basic demonstrations
- **Granite 4.0 Micro** (Q4_K_M) - More capable model for Part 2/3 RAG with complex documents

## Quick Start

### 1. Build the Container Image

```bash
cd Part1-Deploy-LLM
oc new-build --name llama-service --binary --strategy docker
oc start-build llama-service --from-dir=. --follow
```

Or using Docker:
```bash
docker build -t llama-service:dual-model .
```

### 2. Deploy to OpenShift

```bash
# Apply the deployment
oc apply -f llama-deploy.yaml
oc apply -f llama-svc.yaml
oc apply -f llama-route.yaml

# Check the deployment
oc get pods -l app=llama-service
```

### 3. Access the LLM

Get the route URL:
```bash
oc get route llama-service
```

Open the URL in your browser to access the llama.cpp web interface.

## Model Switching

The deployment uses the `LLM_MODEL` environment variable to select which model to use:

### Use TinyLlama (Default - Part 1)

```yaml
env:
  - name: LLM_MODEL
    value: "tinyllama"
```

**Best for:**
- Part 1: Basic LLM demonstrations
- Quick responses
- Lower resource usage
- General conversation and simple tasks

### Use Granite 4.0 (Part 2/3)

```yaml
env:
  - name: LLM_MODEL
    value: "granite"
```

**Best for:**
- Part 2/3: RAG with complex documents
- Technical documentation queries
- Sales manual analysis
- More accurate and detailed responses

### Switch Models at Runtime

You can switch models by updating the deployment:

```bash
# Switch to Granite
oc set env deployment/llama-service LLM_MODEL=granite

# Switch back to TinyLlama
oc set env deployment/llama-service LLM_MODEL=tinyllama

# Check which model is running
oc logs deployment/llama-service | grep "Starting with"
```

## Model Details

### TinyLlama 1.1B Chat v1.0 (Q8_0)
- **Size**: ~1.1GB
- **Parameters**: 1.1 billion
- **Quantization**: Q8_0 (8-bit)
- **Context**: 4096 tokens
- **Source**: https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF

### Granite 4.0 Micro (Q4_K_M)
- **Size**: ~2.5GB
- **Parameters**: ~4 billion
- **Quantization**: Q4_K_M (4-bit)
- **Context**: 4096 tokens
- **Source**: https://huggingface.co/ibm-granite/granite-4.0-micro-GGUF

## Resource Requirements

### Minimum
- **CPU**: 2 cores (Power10 with MMA support)
- **Memory**: 4GB
- **Storage**: 5GB (for both models)

### Recommended
- **CPU**: 4 cores
- **Memory**: 8GB
- **Storage**: 10GB

## Architecture

```
┌─────────────────────────────────┐
│   Container Image               │
│                                 │
│  ┌───────────────────────────┐ │
│  │  llama.cpp server         │ │
│  │  (compiled with OpenBLAS) │ │
│  └───────────┬───────────────┘ │
│              │                  │
│  ┌───────────▼───────────────┐ │
│  │  Startup Script           │ │
│  │  (model selector)         │ │
│  └───────────┬───────────────┘ │
│              │                  │
│      ┌───────┴────────┐        │
│      │                │        │
│  ┌───▼────┐    ┌─────▼─────┐  │
│  │TinyLlama│    │ Granite   │  │
│  │ 1.1B   │    │ 4.0 Micro │  │
│  └────────┘    └───────────┘  │
└─────────────────────────────────┘
```

## Startup Script

The container includes a startup script (`/start-llama.sh`) that:
1. Reads the `LLM_MODEL` environment variable
2. Selects the appropriate model file
3. Starts llama-server with the chosen model

Valid values for `LLM_MODEL`:
- `tinyllama` (default)
- `granite`

## Testing

### Health Check
```bash
curl http://llama-service:8080/health
```

### Test with TinyLlama
```bash
curl http://llama-service:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Hello!"}],
    "temperature": 0.7,
    "max_tokens": 50
  }'
```

### Verify Current Model
```bash
# Check the logs to see which model is loaded
oc logs deployment/llama-service | grep "Starting with"
```

## Troubleshooting

### Pod Not Starting
```bash
# Check pod status
oc describe pod -l app=llama-service

# Check logs
oc logs -l app=llama-service
```

### Model Not Loading
```bash
# Verify models are present in the container
oc exec deployment/llama-service -- ls -lh /models/

# Should show:
# tinyllama-1.1b-chat-v1.0.Q8_0.gguf (~1.1GB)
# granite-4.0-micro-Q4_K_M.gguf (~2.5GB)
```

### Out of Memory
If the pod is killed due to OOM:
1. Increase memory limits in `llama-deploy.yaml`
2. Use TinyLlama instead of Granite (lower memory footprint)

### Slow Responses
1. Ensure running on Power10 nodes with MMA support
2. Check CPU allocation
3. Consider using TinyLlama for faster responses

## Integration with RAG Backend

The RAG backend (from Part 2/3) connects to this LLM service:

```yaml
# In rag-backend deployment
env:
  - name: LLAMA_HOST
    value: "llama-service"
  - name: LLAMA_PORT
    value: "8080"
```

**Recommendation:**
- Use **TinyLlama** for Part 1 demonstrations
- Switch to **Granite** when deploying the RAG backend for Part 2/3

## Files in This Directory

- `Dockerfile` - Multi-model container image with both TinyLlama and Granite
- `llama-deploy.yaml` - Kubernetes deployment with model selection
- `llama-svc.yaml` - Service definition
- `llama-route.yaml` - OpenShift route for external access
- `llama-pvc.yaml` - Persistent volume claim (if needed for additional models)
- `README.md` - This file

## Next Steps

After deploying the LLM service:

1. **Part 1**: Use TinyLlama to demonstrate basic LLM capabilities
   - Show general conversation
   - Demonstrate hallucinations
   - Explain the need for RAG

2. **Part 2**: Deploy Milvus vector database
   - Follow instructions in `Part2-RAG/`

3. **Part 3**: Switch to Granite and deploy RAG backend
   - Update `LLM_MODEL=granite`
   - Deploy consolidated RAG backend
   - Load sales manuals and test RAG queries

## License

Same as parent project.