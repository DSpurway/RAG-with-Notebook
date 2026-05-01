# Part 3 Deployment Guide - RAG with Sales Manuals

## Overview
This guide provides step-by-step instructions for deploying the RAG Sales Manual demo on OpenShift.

## Prerequisites
- OpenShift cluster (e.g., TechZone "OpenShift on POWER10" environment)
- Part 1 (LLM) and Part 2 (Milvus) already deployed
- `oc` CLI tool installed and configured

## Environment Configuration

### Option 1: Using Environment Variables (Recommended)

Each service now supports environment variables for configuration:

**CORS_ORIGIN**: The origin URL for CORS (Cross-Origin Resource Sharing)
- Default: `*` (allows all origins - suitable for development)
- Production: Set to your webpage URL, e.g., `https://rag-webpage-llm-on-techzone.apps.pXXXX.cecc.ihost.com`

**Service-specific URLs** (for RAG-Webpage):
- `RAG_LIST_COLLECTIONS_URL`
- `RAG_DROP_COLLECTION_URL`
- `RAG_LOADER_URL`
- `RAG_GET_DOCS_URL`
- `RAG_PROMPT_LLM_URL`

### Setting Environment Variables in OpenShift

After deploying each service, you can set environment variables:

```bash
# Set CORS origin for a service
oc set env deployment/rag-list-collections CORS_ORIGIN=https://rag-webpage-llm-on-techzone.apps.pXXXX.cecc.ihost.com

# Or use wildcard for development (already the default)
oc set env deployment/rag-list-collections CORS_ORIGIN='*'
```

### Option 2: Auto-Detection (Default Behavior)

The RAG-Webpage service automatically constructs service URLs based on:
- OpenShift namespace (default: `llm-on-techzone`)
- Base domain (default: `apps.cecc.ihost.com`)

You can override these:
```bash
oc set env deployment/rag-webpage NAMESPACE=your-project-name
oc set env deployment/rag-webpage BASE_DOMAIN=apps.pXXXX.cecc.ihost.com
```

## Deployment Steps

### 1. Deploy RAG-List-Collections

```bash
# From OpenShift Web Console:
# 1. Click "+Add" -> "Import from Git"
# 2. Git Repo URL: https://github.com/DSpurway/IBM-Power-RAG-Demos
# 3. Show advanced Git options
# 4. Context dir: /Part3-RAG-Sales-Manual/RAG-List-Collections
# 5. Application: Create new "sales-manual-rag-app"
# 6. Name: rag-list-collections
# 7. Click "Create"

# Optional: Set CORS origin after deployment
oc set env deployment/rag-list-collections CORS_ORIGIN=https://rag-webpage-llm-on-techzone.apps.pXXXX.cecc.ihost.com
```

### 2. Deploy RAG-Drop-Collection

```bash
# Context dir: /Part3-RAG-Sales-Manual/RAG-Drop-Collection
# Application: sales-manual-rag-app (existing)
# Name: rag-drop-collection
```

### 3. Deploy RAG-Loader

```bash
# Context dir: /Part3-RAG-Sales-Manual/RAG-Loader
# Application: sales-manual-rag-app
# Name: rag-loader
```

### 4. Deploy RAG-Get-Docs

```bash
# Context dir: /Part3-RAG-Sales-Manual/RAG-Get-Docs
# Application: sales-manual-rag-app
# Name: rag-get-docs
```

### 5. Deploy RAG-Prompt-LLM

```bash
# Context dir: /Part3-RAG-Sales-Manual/RAG-Prompt-LLM
# Application: sales-manual-rag-app
# Name: rag-prompt-llm
```

### 6. Deploy RAG-Webpage

```bash
# Context dir: /Part3-RAG-Sales-Manual/RAG-Webpage
# Application: sales-manual-rag-app
# Name: rag-webpage

# Optional: Configure service URLs if auto-detection doesn't work
oc set env deployment/rag-webpage \
  RAG_LIST_COLLECTIONS_URL=https://rag-list-collections-llm-on-techzone.apps.pXXXX.cecc.ihost.com \
  RAG_DROP_COLLECTION_URL=https://rag-drop-collection-llm-on-techzone.apps.pXXXX.cecc.ihost.com \
  RAG_LOADER_URL=https://rag-loader-llm-on-techzone.apps.pXXXX.cecc.ihost.com \
  RAG_GET_DOCS_URL=https://rag-get-docs-llm-on-techzone.apps.pXXXX.cecc.ihost.com \
  RAG_PROMPT_LLM_URL=https://rag-prompt-llm-llm-on-techzone.apps.pXXXX.cecc.ihost.com
```

## Quick Setup Script

For faster deployment, you can use the provided setup script:

```bash
# Set your environment number
export TECHZONE_ENV=pXXXX

# Run the setup script
./setup-part3.sh
```

## Verification

1. Check all pods are running:
```bash
oc get pods -l app=sales-manual-rag-app
```

2. Test the webpage:
   - Open the rag-webpage route URL
   - Click "List Collections" - should work without errors
   - If you see CORS errors in browser console, set CORS_ORIGIN environment variables

## Troubleshooting

### CORS Errors
If you see CORS errors in the browser console:
```bash
# Set CORS origin for all services
for service in rag-list-collections rag-drop-collection rag-loader rag-get-docs rag-prompt-llm; do
  oc set env deployment/$service CORS_ORIGIN=https://rag-webpage-llm-on-techzone.apps.pXXXX.cecc.ihost.com
done
```

### Service URLs Not Working
Check the auto-generated config:
```bash
# Get the webpage URL
WEBPAGE_URL=$(oc get route rag-webpage -o jsonpath='{.spec.host}')

# Check the config
curl https://$WEBPAGE_URL/config.js
```

### Timeout Issues
Large PDF files may timeout on the webpage. Check pod logs:
```bash
oc logs -f deployment/rag-loader
oc logs -f deployment/rag-prompt-llm
```

## Improvements in This Version

1. **No More Hardcoded URLs**: All URLs are now configurable via environment variables
2. **Better Error Handling**: Clear error messages and status indicators
3. **Improved UI**: Better visual feedback with loading states and styled messages
4. **Auto-Configuration**: Webpage automatically detects service URLs
5. **Development Mode**: Default wildcard CORS for easier testing

## Next Steps

After deployment:
1. Load the Sales Manual PDFs using the webpage
2. Test queries against the loaded documents
3. Review pod logs for detailed information
4. Customize prompts and questions as needed