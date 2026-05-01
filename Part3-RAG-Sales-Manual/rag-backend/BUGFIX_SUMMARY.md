# RAG Backend Bug Fixes

## Date: April 13, 2026

## Issues Found

When deploying the RAG backend container, it was failing to start with the following errors:

### 1. Missing Module Error
```
ModuleNotFoundError: No module named 'web_scraper'
```

### 2. Deprecated LangChain Imports
```
LangChainDeprecationWarning: Importing embeddings from langchain is deprecated.
Importing from langchain will no longer be supported as of langchain==0.2.0.
Please import from langchain-community instead
```

## Root Causes

1. **Missing File in Docker Image**: The `Dockerfile` was only copying `app.py` but not `web_scraper.py`, causing the import to fail.

2. **Outdated Import Statements**: The code was using deprecated `langchain.*` imports instead of the newer `langchain_community.*` imports.

## Fixes Applied

### Fix 1: Updated Dockerfile (Line 38-39)

**Before:**
```dockerfile
# Copy application code
COPY app.py .
```

**After:**
```dockerfile
# Copy application code
COPY app.py .
COPY web_scraper.py .
```

### Fix 2: Updated Import Statements in app.py (Lines 9-11)

**Before:**
```python
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Milvus
from langchain.document_loaders import PyPDFLoader
```

**After:**
```python
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Milvus
from langchain_community.document_loaders import PyPDFLoader
```

### Fix 3: Made Web Scraping Optional (Lines 30-38)

Since web scraping is a future feature and PDFs are the current focus, made the web scraper import optional:

```python
# Optional web scraping support - only import if available
try:
    from web_scraper import IBMDocsScraper, create_langchain_documents, IBMDocsScraperError
    WEB_SCRAPING_AVAILABLE = True
    logger.info("Web scraping module loaded successfully")
except ImportError:
    WEB_SCRAPING_AVAILABLE = False
    logger.warning("Web scraping module not available. Running in PDF-only mode.")
```

### Fix 4: Added Guards to Web Scraping Endpoints

Added checks at the start of `/api/load-url` and `/api/load-multiple-urls` endpoints:

```python
if not WEB_SCRAPING_AVAILABLE:
    return jsonify({
        'error': 'Web scraping feature not available. Please use PDF loading instead.'
    }), 501
```

## Benefits

1. **Graceful Degradation**: The backend now works without `web_scraper.py`, focusing on PDF functionality
2. **Future-Proof**: Web scraping can be enabled later by simply including the file
3. **No Deprecation Warnings**: Using current LangChain import paths
4. **Clear Error Messages**: Users get helpful 501 responses if they try to use unavailable features

## Testing Recommendations

### 1. Build and Deploy
```bash
cd rag-backend
docker build -t rag-backend:fixed .
```

### 2. Test PDF Loading (Core Functionality)
```bash
curl -X POST http://localhost:8080/api/load-pdf \
  -H "Content-Type: application/json" \
  -d '{
    "server_name": "test-server",
    "collection_name": "demo"
  }'
```

### 3. Verify Web Scraping Returns Proper Error
```bash
curl -X POST http://localhost:8080/api/load-url \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "collection_name": "test"
  }'
```

Expected response:
```json
{
  "error": "Web scraping feature not available. Please use PDF loading instead."
}
```

### 4. Check Logs
```bash
oc logs deployment/rag-backend | grep -E "Web scraping|PDF-only"
```

Should see:
```
WARNING:__main__:Web scraping module not available. Running in PDF-only mode.
```

## Files Modified

| File | Lines Changed | Purpose |
|------|---------------|---------|
| `Dockerfile` | 38-39 | Copy web_scraper.py (for future use) |
| `app.py` | 9-11 | Fix deprecated imports |
| `app.py` | 30-38 | Make web scraping optional |
| `app.py` | 177-181 | Guard load-url endpoint |
| `app.py` | 247-252 | Guard load-multiple-urls endpoint |

## Next Steps

1. **Rebuild the container** with these fixes
2. **Redeploy** to OpenShift/TechZone
3. **Test PDF loading** functionality
4. **Verify** the backend starts successfully
5. **Later**: Add `web_scraper.py` and dependencies when ready for web scraping feature

## Status

✅ **FIXED** - Backend should now start successfully and work with PDF documents  
⏳ **PENDING** - Web scraping feature available when needed in future

## Notes

- The type checker warnings about "possibly unbound" variables are expected and safe - the runtime guards prevent those code paths from executing when the module isn't available
- Web scraping dependencies (beautifulsoup4, lxml) are still in requirements.txt but won't cause issues if web_scraper.py is missing
- The backend is now focused on its core PDF RAG functionality