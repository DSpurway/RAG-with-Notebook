# RAG Backend with OpenSearch - Comprehensive Test Plan

## Document Information
- **Version**: 1.0
- **Date**: April 22, 2026
- **Backend**: RAG Backend with OpenSearch (v3.0.0)
- **Target Environment**: Remote OCP Power10 Instance

## Table of Contents
1. [Overview](#overview)
2. [Test Environment](#test-environment)
3. [Prerequisites](#prerequisites)
4. [Test Phases](#test-phases)
5. [Test Execution Sequence](#test-execution-sequence)
6. [Success Criteria](#success-criteria)
7. [Failure Scenarios](#failure-scenarios)
8. [Test Data Requirements](#test-data-requirements)

---

## Overview

This test plan provides comprehensive testing procedures for the consolidated RAG backend service deployed on OpenShift Container Platform (OCP) running on IBM Power10 architecture. The backend uses OpenSearch for vector storage (similar to IBM Spyre RAG implementation) and integrates with a Llama.cpp-based LLM service.

### Architecture Components
```
┌─────────────────┐
│   Carbon UI     │
│   (Next.js)     │
└────────┬────────┘
         │ HTTPS/REST
         │
┌────────▼────────────┐      ┌──────────────────┐
│  RAG Backend        │◄────►│  OpenSearch      │
│  (Flask/Python)     │      │  (Vector DB)     │
└────────┬────────────┘      └──────────────────┘
         │ HTTP
         │
┌────────▼────────────┐
│  LLM Service        │
│  (llama.cpp)        │
└─────────────────────┘
```

### API Endpoints to Test
- `GET /health` - Health check
- `GET /` - API documentation
- `GET /api/collections` - List collections
- `DELETE /api/collections/<name>` - Drop collection
- `POST /api/load-pdf` - Load PDF documents
- `POST /api/search` - Vector search (dense, sparse, hybrid modes)
- `POST /api/generate` - LLM generation

---

## Test Environment

### Required Services
1. **RAG Backend** (rag-backend-opensearch)
   - Port: 8080
   - Route: `https://rag-backend-opensearch-<namespace>.<domain>`
   
2. **OpenSearch Service** (opensearch-service)
   - Internal port: 9200
   - Credentials: admin/admin (default)
   
3. **LLM Service** (llama-service)
   - Internal port: 8080
   - Model: Llama-based (e.g., Mistral, Llama2)

### Environment Variables
```bash
OPENSEARCH_HOST=opensearch-service
OPENSEARCH_PORT=9200
OPENSEARCH_USERNAME=admin
OPENSEARCH_PASSWORD=admin
OPENSEARCH_DB_PREFIX=rag
OPENSEARCH_USE_SSL=false
LLAMA_HOST=llama-service
LLAMA_PORT=8080
PDF_DIR=/app/pdfs
CORS_ORIGIN=*
```

---

## Prerequisites

### 1. Access Requirements
- [ ] OCP cluster access with appropriate permissions
- [ ] Route URL for rag-backend-opensearch service
- [ ] Network connectivity to OCP cluster
- [ ] `curl` or similar HTTP client installed

### 2. Test Tools
- [ ] Bash shell (Linux/Mac) or PowerShell (Windows)
- [ ] `curl` command-line tool
- [ ] `jq` for JSON parsing (optional but recommended)
- [ ] Text editor for reviewing logs

### 3. Test Data
- [ ] Sample PDF files available in `/app/pdfs` directory:
  - IBM_Power_S1012.pdf
  - IBM_Power_S1014.pdf
  - IBM_Power_S1022.pdf
  - IBM_Power_S1022s.pdf
  - IBM_Power_S1024.pdf

### 4. Configuration
- [ ] Set `RAG_BACKEND_URL` environment variable
- [ ] Verify SSL certificates (or use `-k` flag for self-signed)
- [ ] Confirm namespace and domain settings

---

## Test Phases

### Phase 1: Health and Connectivity
**Objective**: Verify basic service availability and dependencies

**Tests**:
1. **T1.1 - Basic Health Check**
   - Endpoint: `GET /health`
   - Expected: HTTP 200, status="healthy"
   - Validates: Service is running, OpenSearch connected, LLM connected

2. **T1.2 - API Documentation**
   - Endpoint: `GET /`
   - Expected: HTTP 200, JSON with service info and endpoints
   - Validates: Service is responding correctly

3. **T1.3 - OpenSearch Connectivity**
   - Endpoint: `GET /health`
   - Expected: `opensearch: "connected"`
   - Validates: OpenSearch cluster is accessible

4. **T1.4 - LLM Service Connectivity**
   - Endpoint: `GET /health`
   - Expected: `llm: "connected"`
   - Validates: LLM service is accessible

**Success Criteria**:
- All health checks return HTTP 200
- OpenSearch status is "connected"
- LLM status is "connected" (or "disconnected" if LLM not critical)
- Response time < 5 seconds

**Failure Scenarios**:
- HTTP 503: Service degraded (OpenSearch disconnected)
- HTTP 500: Internal server error
- Timeout: Service not responding
- Connection refused: Service not running

---

### Phase 2: Collection Management
**Objective**: Test OpenSearch index/collection operations

**Tests**:
1. **T2.1 - List Empty Collections**
   - Endpoint: `GET /api/collections`
   - Expected: HTTP 200, empty array or existing collections
   - Validates: Can query OpenSearch indices

2. **T2.2 - Create Collection (via PDF load)**
   - Endpoint: `POST /api/load-pdf`
   - Payload: `{"server_name": "IBM_Power_S1012", "collection_name": "test_collection"}`
   - Expected: HTTP 200, success=true
   - Validates: Can create new OpenSearch index

3. **T2.3 - List Collections After Creation**
   - Endpoint: `GET /api/collections`
   - Expected: HTTP 200, array contains "rag_<hash>" index
   - Validates: Collection was created successfully

4. **T2.4 - Drop Collection**
   - Endpoint: `DELETE /api/collections/test_collection`
   - Expected: HTTP 200, success=true
   - Validates: Can delete OpenSearch index

5. **T2.5 - Verify Collection Dropped**
   - Endpoint: `GET /api/collections`
   - Expected: HTTP 200, collection not in list
   - Validates: Collection was removed

**Success Criteria**:
- Can list collections without errors
- Can create collections via PDF loading
- Can drop collections successfully
- Collection list updates correctly after operations

**Failure Scenarios**:
- HTTP 404: Collection not found (for drop operation)
- HTTP 500: OpenSearch operation failed
- Inconsistent state: Collection appears in list after drop

---

### Phase 3: PDF Document Loading
**Objective**: Test PDF ingestion and embedding generation

**Tests**:
1. **T3.1 - Load Small PDF**
   - Endpoint: `POST /api/load-pdf`
   - Payload: `{"server_name": "IBM_Power_S1012", "collection_name": "sales_manuals"}`
   - Expected: HTTP 200, chunks > 0
   - Validates: Can load and process PDF

2. **T3.2 - Load Multiple PDFs to Same Collection**
   - Endpoint: `POST /api/load-pdf` (multiple calls)
   - Payloads: Different server_name values
   - Expected: HTTP 200 for each, cumulative chunks
   - Validates: Can append to existing collection

3. **T3.3 - Load Large PDF**
   - Endpoint: `POST /api/load-pdf`
   - Payload: `{"server_name": "IBM_Power_S1024", "collection_name": "sales_manuals"}`
   - Expected: HTTP 200, chunks > 100
   - Validates: Can handle larger documents
   - Note: May take 30-60 seconds

4. **T3.4 - Load Non-Existent PDF**
   - Endpoint: `POST /api/load-pdf`
   - Payload: `{"server_name": "NonExistent", "collection_name": "test"}`
   - Expected: HTTP 404, error message
   - Validates: Proper error handling

5. **T3.5 - Load PDF Without server_name**
   - Endpoint: `POST /api/load-pdf`
   - Payload: `{"collection_name": "test"}`
   - Expected: HTTP 400, error="server_name is required"
   - Validates: Input validation

**Success Criteria**:
- PDFs are loaded and split into chunks
- Embeddings are generated (384-dimensional vectors)
- Documents are indexed in OpenSearch
- Metadata is preserved (filename, page numbers, etc.)
- Response includes chunk count

**Failure Scenarios**:
- HTTP 404: PDF file not found
- HTTP 400: Missing required parameters
- HTTP 500: Embedding generation failed
- HTTP 500: OpenSearch indexing failed
- Timeout: Large PDF processing exceeded timeout

---

### Phase 4: Vector Search
**Objective**: Test semantic search functionality

**Tests**:
1. **T4.1 - Dense Vector Search**
   - Endpoint: `POST /api/search`
   - Payload: `{"question": "How many processors?", "collection_name": "sales_manuals", "k": 3, "mode": "dense"}`
   - Expected: HTTP 200, 3 results with scores
   - Validates: k-NN vector search works

2. **T4.2 - Sparse Keyword Search**
   - Endpoint: `POST /api/search`
   - Payload: `{"question": "processor specifications", "collection_name": "sales_manuals", "k": 3, "mode": "sparse"}`
   - Expected: HTTP 200, 3 results with scores
   - Validates: BM25 keyword search works

3. **T4.3 - Hybrid Search (Default)**
   - Endpoint: `POST /api/search`
   - Payload: `{"question": "What are the memory options?", "collection_name": "sales_manuals", "k": 3}`
   - Expected: HTTP 200, 3 results with combined scores
   - Validates: Hybrid search pipeline works

4. **T4.4 - Search with Different k Values**
   - Endpoint: `POST /api/search`
   - Payloads: k=1, k=5, k=10
   - Expected: HTTP 200, correct number of results
   - Validates: Result count parameter works

5. **T4.5 - Search Non-Existent Collection**
   - Endpoint: `POST /api/search`
   - Payload: `{"question": "test", "collection_name": "nonexistent", "k": 3}`
   - Expected: HTTP 404, error message
   - Validates: Collection existence check

6. **T4.6 - Search Without Question**
   - Endpoint: `POST /api/search`
   - Payload: `{"collection_name": "sales_manuals", "k": 3}`
   - Expected: HTTP 400, error="question is required"
   - Validates: Input validation

7. **T4.7 - Verify Result Quality**
   - Endpoint: `POST /api/search`
   - Payload: `{"question": "IBM Power S1012 processor count", "collection_name": "sales_manuals", "k": 3}`
   - Expected: Results contain relevant information about S1012
   - Validates: Semantic relevance

**Success Criteria**:
- Search returns relevant results
- Scores are reasonable (0.0 to 1.0 range)
- Results include content and metadata
- Different search modes work correctly
- Response time < 10 seconds

**Failure Scenarios**:
- HTTP 404: Collection not found
- HTTP 400: Missing required parameters
- HTTP 500: Search query failed
- Empty results: No relevant documents found
- Low scores: Poor semantic matching

---

### Phase 5: LLM Integration
**Objective**: Test LLM generation with RAG context

**Tests**:
1. **T5.1 - Simple Generation**
   - Endpoint: `POST /api/generate`
   - Payload: `{"prompt": "What is 2+2?", "temperature": 0.1, "n_predict": 50}`
   - Expected: HTTP 200, content with answer
   - Validates: Basic LLM connectivity

2. **T5.2 - RAG-Enhanced Generation**
   - Steps:
     a. Search: `POST /api/search` with question
     b. Build prompt with context from search results
     c. Generate: `POST /api/generate` with enhanced prompt
   - Expected: HTTP 200, contextual answer
   - Validates: End-to-end RAG workflow

3. **T5.3 - Generation with Different Temperatures**
   - Endpoint: `POST /api/generate`
   - Payloads: temperature=0.1, 0.5, 0.9
   - Expected: HTTP 200, varying creativity
   - Validates: Temperature parameter works

4. **T5.4 - Generation with Different n_predict**
   - Endpoint: `POST /api/generate`
   - Payloads: n_predict=50, 100, 200
   - Expected: HTTP 200, varying response lengths
   - Validates: Token limit parameter works

5. **T5.5 - Generation Without Prompt**
   - Endpoint: `POST /api/generate`
   - Payload: `{"temperature": 0.1}`
   - Expected: HTTP 400, error="prompt is required"
   - Validates: Input validation

6. **T5.6 - Long Generation (Timeout Test)**
   - Endpoint: `POST /api/generate`
   - Payload: `{"prompt": "Explain...", "n_predict": 500}`
   - Expected: HTTP 200 or HTTP 504 (timeout)
   - Validates: Timeout handling

**Success Criteria**:
- LLM generates coherent responses
- RAG context improves answer quality
- Parameters affect output as expected
- Response includes timing information
- Timeout handling works correctly

**Failure Scenarios**:
- HTTP 400: Missing prompt
- HTTP 500: LLM service error
- HTTP 504: Request timeout (>60 seconds)
- Empty content: Generation failed
- Irrelevant answer: Context not used

---

### Phase 6: Data Persistence
**Objective**: Verify data survives pod restarts

**Tests**:
1. **T6.1 - Load Data**
   - Load PDFs into a test collection
   - Verify data is searchable

2. **T6.2 - Restart RAG Backend Pod**
   - Delete pod: `oc delete pod -l app=rag-backend-opensearch`
   - Wait for new pod to start
   - Verify health check passes

3. **T6.3 - Verify Data After Restart**
   - List collections: Should still exist
   - Search: Should return same results
   - Validates: OpenSearch data persists

4. **T6.4 - Restart OpenSearch Pod**
   - Delete pod: `oc delete pod -l app=opensearch`
   - Wait for new pod to start
   - Verify RAG backend reconnects

5. **T6.5 - Verify Data After OpenSearch Restart**
   - List collections: Should still exist
   - Search: Should return same results
   - Validates: OpenSearch PVC works

**Success Criteria**:
- Collections survive RAG backend restart
- Collections survive OpenSearch restart
- Search results are consistent
- No data loss
- Automatic reconnection works

**Failure Scenarios**:
- Collections disappear after restart
- Search returns different results
- Connection errors after restart
- Data corruption

---

### Phase 7: Error Handling and Edge Cases
**Objective**: Test system behavior under error conditions

**Tests**:
1. **T7.1 - Invalid JSON Payload**
   - Send malformed JSON
   - Expected: HTTP 400, error message

2. **T7.2 - Missing Content-Type Header**
   - Send POST without Content-Type
   - Expected: HTTP 400 or 415

3. **T7.3 - Very Large Payload**
   - Send extremely large JSON
   - Expected: HTTP 413 or timeout

4. **T7.4 - Concurrent Requests**
   - Send multiple requests simultaneously
   - Expected: All succeed or queue properly

5. **T7.5 - OpenSearch Disconnection**
   - Stop OpenSearch service
   - Expected: HTTP 503, degraded status

6. **T7.6 - LLM Disconnection**
   - Stop LLM service
   - Expected: HTTP 500 or 504 for generate

7. **T7.7 - Special Characters in Input**
   - Send queries with special characters
   - Expected: Proper escaping and handling

8. **T7.8 - Empty Collection Search**
   - Search in empty collection
   - Expected: HTTP 200, empty results

**Success Criteria**:
- Graceful error handling
- Informative error messages
- No crashes or hangs
- Proper HTTP status codes
- Service remains available

**Failure Scenarios**:
- Service crashes
- Unclear error messages
- Wrong HTTP status codes
- Memory leaks
- Deadlocks

---

## Test Execution Sequence

### Recommended Order
1. **Phase 1**: Health and Connectivity (prerequisite for all)
2. **Phase 2**: Collection Management (setup for later tests)
3. **Phase 3**: PDF Document Loading (creates test data)
4. **Phase 4**: Vector Search (uses loaded data)
5. **Phase 5**: LLM Integration (end-to-end workflow)
6. **Phase 6**: Data Persistence (requires existing data)
7. **Phase 7**: Error Handling (can run anytime)

### Dependencies
```
Phase 1 (Health)
    ↓
Phase 2 (Collections) → Phase 3 (PDF Loading)
                            ↓
                        Phase 4 (Search) → Phase 5 (LLM)
                            ↓
                        Phase 6 (Persistence)
                            
Phase 7 (Error Handling) - Independent
```

---

## Success Criteria

### Overall System Health
- [ ] All services are running and healthy
- [ ] OpenSearch cluster is green
- [ ] LLM service is responsive
- [ ] No error logs in pods

### Functional Requirements
- [ ] Can create and manage collections
- [ ] Can load PDF documents successfully
- [ ] Can perform vector search with good results
- [ ] Can generate LLM responses
- [ ] Data persists across restarts

### Performance Requirements
- [ ] Health check: < 5 seconds
- [ ] PDF loading: < 60 seconds per document
- [ ] Search: < 10 seconds
- [ ] LLM generation: < 60 seconds
- [ ] Collection operations: < 5 seconds

### Quality Requirements
- [ ] Search results are semantically relevant
- [ ] LLM responses are coherent and contextual
- [ ] Error messages are clear and actionable
- [ ] No data loss or corruption
- [ ] Consistent behavior across restarts

---

## Failure Scenarios

### Critical Failures (Block Deployment)
1. **Health Check Fails**
   - Symptom: HTTP 503 or timeout
   - Impact: Service not operational
   - Action: Check pod logs, verify dependencies

2. **Cannot Load PDFs**
   - Symptom: HTTP 500 on load-pdf
   - Impact: Cannot ingest data
   - Action: Check PDF directory, embeddings model, OpenSearch

3. **Search Returns No Results**
   - Symptom: Empty results for known queries
   - Impact: RAG not functional
   - Action: Verify data loaded, check embeddings

4. **LLM Not Responding**
   - Symptom: HTTP 504 or 500 on generate
   - Impact: Cannot generate answers
   - Action: Check LLM service, model loaded

5. **Data Loss After Restart**
   - Symptom: Collections disappear
   - Impact: Not production-ready
   - Action: Check PVC, OpenSearch configuration

### Non-Critical Failures (Can Deploy with Warnings)
1. **Slow Performance**
   - Symptom: Responses > expected time
   - Impact: Poor user experience
   - Action: Optimize, scale resources

2. **LLM Timeouts**
   - Symptom: Occasional 504 errors
   - Impact: Some requests fail
   - Action: Increase timeout, optimize prompts

3. **Low Search Relevance**
   - Symptom: Results not very relevant
   - Impact: Reduced quality
   - Action: Tune search parameters, improve chunking

---

## Test Data Requirements

### PDF Documents
Located in `/app/pdfs/` directory:
- **IBM_Power_S1012.pdf** - Small document (~10-20 pages)
- **IBM_Power_S1014.pdf** - Medium document (~30-50 pages)
- **IBM_Power_S1022.pdf** - Medium document
- **IBM_Power_S1022s.pdf** - Medium document
- **IBM_Power_S1024.pdf** - Large document (~100+ pages)

### Test Questions
Use these questions for search and RAG testing:
1. "How many processors does the IBM Power S1012 support?"
2. "What are the memory specifications for the S1014?"
3. "What is the maximum storage capacity?"
4. "What operating systems are supported?"
5. "What are the power requirements?"

### Expected Results
- S1012: 1-2 processors
- S1014: 4-8 processors
- S1022: 8-16 processors
- S1024: 16-24 processors

---

## Test Execution Scripts

All test scripts are provided in the `tests/` directory:
- `test-health.sh` - Phase 1 tests
- `test-collections.sh` - Phase 2 tests (included in test-pdf-loading.sh)
- `test-pdf-loading.sh` - Phase 3 tests
- `test-search.sh` - Phase 4 tests
- `test-llm-integration.sh` - Phase 5 tests
- `test-persistence.sh` - Phase 6 tests
- `test-error-handling.sh` - Phase 7 tests (included in test-all.sh)
- `test-all.sh` - Master script running all tests

### Configuration
Set environment variable before running:
```bash
export RAG_BACKEND_URL="https://rag-backend-opensearch-<namespace>.<domain>"
```

Or pass as parameter:
```bash
./test-health.sh https://rag-backend-opensearch-<namespace>.<domain>
```

---

## Appendix A: API Reference

### Health Check
```bash
GET /health
Response: {
  "status": "healthy",
  "opensearch": "connected",
  "llm": "connected"
}
```

### List Collections
```bash
GET /api/collections
Response: {
  "success": true,
  "collections": ["rag_abc123", "rag_def456"]
}
```

### Load PDF
```bash
POST /api/load-pdf
Content-Type: application/json
{
  "server_name": "IBM_Power_S1012",
  "collection_name": "sales_manuals"
}
Response: {
  "success": true,
  "message": "Successfully loaded IBM_Power_S1012",
  "chunks": 42,
  "collection": "sales_manuals"
}
```

### Search
```bash
POST /api/search
Content-Type: application/json
{
  "question": "How many processors?",
  "collection_name": "sales_manuals",
  "k": 3,
  "mode": "hybrid"
}
Response: {
  "success": true,
  "results": [
    {
      "content": "...",
      "metadata": {...},
      "score": 0.85
    }
  ],
  "count": 3
}
```

### Generate
```bash
POST /api/generate
Content-Type: application/json
{
  "prompt": "Based on the context...",
  "temperature": 0.1,
  "n_predict": 100
}
Response: {
  "success": true,
  "content": "The answer is...",
  "timings": {...}
}
```

---

## Appendix B: Troubleshooting Guide

### Common Issues

**Issue**: Health check returns 503
- **Cause**: OpenSearch not connected
- **Solution**: Check OpenSearch pod, verify credentials

**Issue**: PDF loading fails with 404
- **Cause**: PDF file not found
- **Solution**: Verify PDF exists in /app/pdfs, check filename

**Issue**: Search returns empty results
- **Cause**: No data loaded or wrong collection name
- **Solution**: Load PDFs first, verify collection name

**Issue**: LLM generation times out
- **Cause**: LLM service slow or not responding
- **Solution**: Check LLM pod, reduce n_predict value

**Issue**: Collections disappear after restart
- **Cause**: OpenSearch PVC not configured
- **Solution**: Check PVC exists and is bound

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-04-22 | Bob | Initial comprehensive test plan for OpenSearch backend |

---

**End of Test Plan**