# RAG Backend Testing Suite

Comprehensive testing scripts for the RAG Backend with OpenSearch deployed on OpenShift Container Platform (OCP) Power10.

## Overview

This testing suite provides automated tests for validating the RAG backend service functionality, including:
- Health checks and connectivity
- PDF document loading
- Vector search (dense, sparse, hybrid)
- LLM integration and generation
- Data persistence
- Error handling

## Prerequisites

### Required
- **Windows PowerShell 5.1+** or **PowerShell Core 7+**
- **Network access** to your OCP cluster
- **RAG Backend Route URL** (external OCP route)

### Optional
- **oc CLI** (for persistence tests that restart pods)
- **Git Bash** or **WSL** (if you prefer bash scripts)

## Quick Start

### 1. Get Your RAG Backend URL

Find your RAG backend's external route URL:

```powershell
# Using oc CLI
oc get route rag-backend-opensearch -n <namespace>

# Example output:
# NAME                      HOST/PORT
# rag-backend-opensearch    rag-backend-opensearch-llm-on-techzone.apps.p1234.cecc.ihost.com
```

Your URL will be: `https://rag-backend-opensearch-llm-on-techzone.apps.p1234.cecc.ihost.com`

### 2. Set Environment Variable (Optional)

```powershell
# Set for current session
$env:RAG_BACKEND_URL = "https://rag-backend-opensearch-<namespace>.<domain>"

# Or set permanently (Windows)
[System.Environment]::SetEnvironmentVariable('RAG_BACKEND_URL', 'https://your-url-here', 'User')
```

### 3. Run Tests

```powershell
# Navigate to tests directory
cd C:\Users\<your-user>\EMEA-AI-SQUAD\RAG-with-Notebook\rag-backend\tests

# Run individual test
.\Test-Health.ps1 -RagBackendUrl "https://your-backend-url"

# Or use environment variable
.\Test-Health.ps1

# Run all tests
.\Test-All.ps1 -RagBackendUrl "https://your-backend-url"
```

## Test Scripts

### Test-Health.ps1
**Phase 1: Health and Connectivity**

Tests basic service availability and dependencies.

```powershell
.\Test-Health.ps1 -RagBackendUrl "https://your-url" [-Verbose]
```

**Tests:**
- T1.1 - Basic Health Check
- T1.2 - API Documentation
- T1.3 - OpenSearch Connectivity
- T1.4 - LLM Service Connectivity
- T1.5 - Response Time Check
- T1.6 - CORS Headers Check

**Expected Duration:** 10-30 seconds

---

### Test-PdfLoading.ps1
**Phase 2 & 3: Collection Management and PDF Loading**

Tests PDF document ingestion and OpenSearch index management.

```powershell
.\Test-PdfLoading.ps1 -RagBackendUrl "https://your-url" [-TestCollection "my_collection"]
```

**Tests:**
- T2.1 - List Collections
- T2.2 - Drop Test Collection (Cleanup)
- T3.1 - Load Small PDF (IBM_Power_S1012)
- T3.2 - Load Second PDF (IBM_Power_S1014)
- T3.3 - Verify Collection Exists
- T3.4 - Load Non-Existent PDF (Error Handling)
- T3.5 - Load Without server_name (Validation)
- T3.6 - Load Large PDF (Optional, may timeout)

**Expected Duration:** 2-5 minutes

---

### Test-Search.ps1
**Phase 4: Vector Search**

Tests semantic search functionality with different modes.

```powershell
.\Test-Search.ps1 -RagBackendUrl "https://your-url" [-SearchK 3]
```

**Tests:**
- T4.1 - Dense Vector Search (k-NN)
- T4.2 - Sparse Keyword Search (BM25)
- T4.3 - Hybrid Search (Default)
- T4.4 - Search with Different K Values
- T4.5 - Search Non-Existent Collection
- T4.6 - Search Without Question (Validation)
- T4.7 - Verify Result Quality
- T4.8 - Search with Special Characters
- T4.9 - Search Response Time

**Expected Duration:** 1-2 minutes

**Prerequisites:** Run Test-PdfLoading.ps1 first to create test data

---

### Test-LlmIntegration.ps1
**Phase 5: LLM Integration**

Tests LLM generation and end-to-end RAG workflow.

```powershell
.\Test-LlmIntegration.ps1 -RagBackendUrl "https://your-url" [-LlmTemperature 0.1] [-LlmNPredict 100]
```

**Tests:**
- T5.1 - Simple LLM Generation
- T5.2 - RAG-Enhanced Generation (End-to-End)
- T5.3 - Generation with Different Temperatures
- T5.4 - Generation with Different n_predict
- T5.5 - Generation Without Prompt (Validation)
- T5.6 - Long Generation (Timeout Handling)
- T5.7 - Generation Response Time
- T5.8 - Verify Context Improves Answer Quality

**Expected Duration:** 2-5 minutes

**Prerequisites:** Run Test-PdfLoading.ps1 first to create test data

---

### Test-Persistence.ps1
**Phase 6: Data Persistence**

Tests data survival across pod restarts.

```powershell
.\Test-Persistence.ps1 -RagBackendUrl "https://your-url" [-Namespace "llm-on-techzone"]
```

**Tests:**
- T6.1 - Load Test Data
- T6.2 - Restart RAG Backend Pod
- T6.3 - Verify Data After Backend Restart
- T6.4 - Restart OpenSearch Pod
- T6.5 - Verify Data After OpenSearch Restart

**Expected Duration:** 5-10 minutes

**Prerequisites:** 
- oc CLI installed and logged in
- Permissions to delete pods in namespace

---

### Test-All.ps1
**Master Test Script**

Runs all test phases in sequence.

```powershell
.\Test-All.ps1 -RagBackendUrl "https://your-url" [-SkipPersistence]
```

**Options:**
- `-SkipPersistence` - Skip persistence tests (no pod restarts)
- `-StopOnFailure` - Stop if any test phase fails
- `-Verbose` - Show detailed output

**Expected Duration:** 10-20 minutes (5-10 minutes with -SkipPersistence)

## Parameters

### Common Parameters

All test scripts support these parameters:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `RagBackendUrl` | string | `$env:RAG_BACKEND_URL` | External OCP route URL |
| `SkipCertificateCheck` | switch | `$true` | Skip SSL certificate validation |
| `TimeoutSeconds` | int | `60-120` | Request timeout in seconds |
| `Verbose` | switch | `$false` | Enable verbose output |

### Script-Specific Parameters

**Test-PdfLoading.ps1:**
- `TestCollection` (string): Collection name for tests (default: "test_sales_manuals")

**Test-Search.ps1:**
- `SearchK` (int): Number of search results to retrieve (default: 3)
- `TestCollection` (string): Collection to search (default: "test_sales_manuals")

**Test-LlmIntegration.ps1:**
- `LlmTemperature` (double): LLM temperature 0.0-1.0 (default: 0.1)
- `LlmNPredict` (int): Max tokens to generate (default: 100)
- `TestCollection` (string): Collection for RAG context (default: "test_sales_manuals")

**Test-Persistence.ps1:**
- `Namespace` (string): OCP namespace (default: "llm-on-techzone")
- `TestCollection` (string): Collection for persistence test (default: "persistence_test")

## Usage Examples

### Basic Health Check
```powershell
.\Test-Health.ps1 -RagBackendUrl "https://rag-backend-opensearch-llm-on-techzone.apps.p1234.cecc.ihost.com"
```

### Load PDFs and Test Search
```powershell
# Load PDFs
.\Test-PdfLoading.ps1 -RagBackendUrl "https://your-url"

# Test search
.\Test-Search.ps1 -RagBackendUrl "https://your-url" -SearchK 5
```

### End-to-End RAG Test
```powershell
# Load data
.\Test-PdfLoading.ps1 -RagBackendUrl "https://your-url"

# Test RAG workflow
.\Test-LlmIntegration.ps1 -RagBackendUrl "https://your-url" -Verbose
```

### Run All Tests (Skip Persistence)
```powershell
.\Test-All.ps1 -RagBackendUrl "https://your-url" -SkipPersistence
```

### Run All Tests with Verbose Output
```powershell
.\Test-All.ps1 -RagBackendUrl "https://your-url" -Verbose
```

## Interpreting Results

### Test Output

Each test displays:
- **✓ PASS** (Green): Test passed successfully
- **✗ FAIL** (Red): Test failed
- **INFO** (Cyan): Informational messages
- **WARNING** (Yellow): Non-critical issues

### Exit Codes

- `0`: All tests passed
- `1`: One or more tests failed

### Example Output

```
========================================
RAG Backend Health Check Tests
========================================
Backend URL: https://rag-backend-opensearch-llm-on-techzone.apps.p1234.cecc.ihost.com
SSL Verify: Disabled
Timeout: 60s

TEST: T1.1 - Basic Health Check
✓ PASS: Health endpoint returned 200 with valid response

TEST: T1.2 - API Documentation
✓ PASS: API documentation endpoint working

TEST: T1.3 - OpenSearch Connectivity
✓ PASS: OpenSearch is connected

TEST: T1.4 - LLM Service Connectivity
✓ PASS: LLM service is connected

TEST: T1.5 - Response Time Check
✓ PASS: Response time: 1.23s (< 5s threshold)

TEST: T1.6 - CORS Headers Check
✓ PASS: Test passed (CORS not critical for backend testing)

========================================
TEST SUMMARY
========================================
Total Tests: 6
Passed: 6
Failed: 0

All tests passed!
```

## Troubleshooting

### Common Issues

#### 1. "Cannot connect to the remote server"
**Cause:** Network connectivity issue or wrong URL

**Solution:**
```powershell
# Verify URL is correct
$env:RAG_BACKEND_URL

# Test basic connectivity
Test-NetConnection -ComputerName "rag-backend-opensearch-namespace.apps.domain.com" -Port 443

# Check if route exists
oc get route rag-backend-opensearch
```

#### 2. "The underlying connection was closed: Could not establish trust relationship"
**Cause:** SSL certificate validation failing

**Solution:**
```powershell
# Use -SkipCertificateCheck (default is $true)
.\Test-Health.ps1 -RagBackendUrl "https://your-url" -SkipCertificateCheck
```

#### 3. "OpenSearch status: disconnected"
**Cause:** OpenSearch service not running or not accessible

**Solution:**
```powershell
# Check OpenSearch pod
oc get pods -l app=opensearch

# Check OpenSearch logs
oc logs -l app=opensearch --tail=50

# Restart OpenSearch if needed
oc delete pod -l app=opensearch
```

#### 4. "LLM status: disconnected"
**Cause:** LLM service not running or not accessible

**Solution:**
```powershell
# Check LLM pod
oc get pods -l app=llama-service

# Check LLM logs
oc logs -l app=llama-service --tail=50

# Note: Some tests can pass without LLM
```

#### 5. "PDF not found" errors
**Cause:** PDF files not present in container

**Solution:**
```powershell
# Check if PDFs exist in pod
oc exec -it deployment/rag-backend-opensearch -- ls -la /app/pdfs/

# If missing, rebuild container with PDFs
```

#### 6. Test timeouts
**Cause:** Operations taking longer than timeout

**Solution:**
```powershell
# Increase timeout
.\Test-PdfLoading.ps1 -RagBackendUrl "https://your-url" -TimeoutSeconds 180

# Check pod logs for actual progress
oc logs -f deployment/rag-backend-opensearch
```

### PowerShell Execution Policy

If you get "cannot be loaded because running scripts is disabled":

```powershell
# Check current policy
Get-ExecutionPolicy

# Set policy for current user (recommended)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Or bypass for single script
PowerShell -ExecutionPolicy Bypass -File .\Test-Health.ps1 -RagBackendUrl "https://your-url"
```

## Test Data

### PDF Documents

The tests expect these PDFs in `/app/pdfs/` directory:
- `IBM_Power_S1012.pdf` - Small document (~10-20 pages)
- `IBM_Power_S1014.pdf` - Medium document (~30-50 pages)
- `IBM_Power_S1022.pdf` - Medium document
- `IBM_Power_S1022s.pdf` - Medium document
- `IBM_Power_S1024.pdf` - Large document (~100+ pages)

### Test Questions

The scripts use these questions for testing:
1. "How many processors does the IBM Power S1012 support?"
2. "What are the memory specifications?"
3. "What is the maximum storage capacity?"
4. "What operating systems are supported?"
5. "What are the power requirements?"

## CI/CD Integration

### Azure DevOps Pipeline

```yaml
steps:
- task: PowerShell@2
  displayName: 'Run RAG Backend Tests'
  inputs:
    targetType: 'filePath'
    filePath: '$(System.DefaultWorkingDirectory)/rag-backend/tests/Test-All.ps1'
    arguments: '-RagBackendUrl "$(RAG_BACKEND_URL)" -SkipPersistence'
    errorActionPreference: 'stop'
    failOnStderr: true
```

### GitHub Actions

```yaml
- name: Run RAG Backend Tests
  shell: pwsh
  run: |
    cd rag-backend/tests
    ./Test-All.ps1 -RagBackendUrl "${{ secrets.RAG_BACKEND_URL }}" -SkipPersistence
```

## Additional Resources

- **Test Plan**: See [TEST_PLAN.md](TEST_PLAN.md) for detailed test specifications
- **API Documentation**: Access `https://your-backend-url/` for API reference
- **OpenSearch Docs**: [OpenSearch Documentation](https://opensearch.org/docs/latest/)
- **Spyre RAG Reference**: [IBM project-ai-services](https://github.com/IBM/project-ai-services/tree/main/spyre-rag)

## Support

For issues or questions:
1. Check the [Troubleshooting](#troubleshooting) section
2. Review pod logs: `oc logs -f deployment/rag-backend-opensearch`
3. Check OpenSearch logs: `oc logs -f deployment/opensearch`
4. Verify network connectivity and routes

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-04-22 | Initial PowerShell test suite for OpenSearch backend |

---

**Note:** These tests are designed for the OpenSearch-based RAG backend. If you're using the ChromaDB version, some tests may need adjustment.