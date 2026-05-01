# Docling Integration Implementation Plan
## RAG-with-Notebook Backend Enhancement

**Version:** 1.0  
**Date:** 2026-04-22  
**Status:** Planning Phase

---

## Executive Summary

This document outlines a comprehensive plan to integrate Docling-based PDF processing into the RAG-with-Notebook backend, replacing the current basic PyPDF implementation with a sophisticated hierarchical chunking system inspired by the spyre-rag project.

**Key Objectives:**
- Replace PyPDF with Docling for superior PDF-to-Markdown conversion
- Implement hierarchical chunking with token-based splitting
- Add table extraction and processing capabilities
- Preserve document structure (chapters, sections, subsections)
- Add online PDF download functionality
- Maintain backward compatibility with existing API

**Expected Benefits:**
- Better document structure preservation
- Improved table extraction and understanding
- More intelligent chunking based on document hierarchy
- Enhanced metadata tracking for better retrieval
- Support for loading PDFs from IBM documentation URLs

---

## Table of Contents

1. [Current State Analysis](#1-current-state-analysis)
2. [Architecture Design](#2-architecture-design)
3. [Dependencies](#3-dependencies)
4. [Code Changes Required](#4-code-changes-required)
5. [Implementation Steps](#5-implementation-steps)
6. [Configuration](#6-configuration)
7. [Testing Strategy](#7-testing-strategy)
8. [Deployment Considerations](#8-deployment-considerations)
9. [Risk Assessment](#9-risk-assessment)
10. [Success Criteria](#10-success-criteria)

---

## 1. Current State Analysis

### 1.1 Current Implementation

**Location:** `C:\Users\029878866\EMEA-AI-SQUAD\RAG-with-Notebook\rag-backend\`

**Current PDF Processing Flow:**
```python
# app.py lines 137-145
loader = PyPDFLoader(pdf_path)
docs = loader.load()

text_splitter = CharacterTextSplitter(
    separator="\n",
    chunk_size=768,
    chunk_overlap=0
)
docs = text_splitter.split_documents(docs)
```

**Limitations:**
- ❌ No structure preservation (chapters, sections lost)
- ❌ No table extraction
- ❌ Simple character-based splitting (no token awareness)
- ❌ No chunk overlap (overlap=0)
- ❌ No hierarchical metadata
- ❌ No online PDF download capability

### 1.2 Reference Implementation (spyre-rag)

**Location:** `C:\Users\029878866\EMEA-AI-SQUAD\project-ai-services\spyre-rag\`

**Key Features to Adopt:**
- ✅ Docling-based PDF conversion with structure preservation
- ✅ Hierarchical chunking (chapter → section → subsection → subsubsection)
- ✅ Token-based splitting with configurable overlap (50 tokens)
- ✅ Table extraction with HTML preservation and LLM summarization
- ✅ Font-size based header detection fallback
- ✅ Metadata-rich chunks with page ranges and source nodes

**Key Files:**
- `pdf_utils.py` - Docling conversion, TOC extraction
- `doc_utils.py` - Hierarchical chunking logic
- `config.py` - Configuration parameters

---

## 2. Architecture Design

### 2.1 High-Level Architecture

```
┌─────────────────┐
│   Flask API     │
└────────┬────────┘
         │
    ┌────▼────┐
    │ PDF     │
    │ Source  │
    └────┬────┘
         │
    ┌────▼────────────────┐
    │ Docling Converter   │
    └────┬────────────────┘
         │
    ┌────▼────────────────┐
    │ Structure Extractor │
    └────┬────────────────┘
         │
    ┌────▼──────────┬──────────┐
    │ Text          │ Table    │
    │ Processor     │ Processor│
    └────┬──────────┴──────┬───┘
         │                 │
    ┌────▼─────────────────▼───┐
    │ Hierarchical Chunker     │
    └────┬─────────────────────┘
         │
    ┌────▼─────────────────────┐
    │ Metadata Enricher        │
    └────┬─────────────────────┘
         │
    ┌────▼─────────────────────┐
    │ ChromaDB Ingestion       │
    └──────────────────────────┘
```

### 2.2 Module Structure

**New Modules to Create:**

```
rag-backend/
├── app.py                          # Main Flask app (MODIFY)
├── requirements.txt                # Dependencies (MODIFY)
├── Dockerfile                      # Build config (MODIFY)
├── utils/                          # NEW DIRECTORY
│   ├── __init__.py
│   ├── docling_converter.py       # Docling conversion wrapper
│   ├── pdf_processor.py            # PDF processing orchestrator
│   ├── hierarchical_chunker.py    # Hierarchical chunking logic
│   ├── table_processor.py         # Table extraction & summarization
│   ├── token_utils.py             # Token counting utilities
│   └── pdf_downloader.py          # Online PDF download
├── config/                         # NEW DIRECTORY
│   ├── __init__.py
│   └── docling_config.py          # Docling configuration
└── tests/                          # EXPAND
    ├── test_docling_converter.py
    ├── test_hierarchical_chunker.py
    ├── test_table_processor.py
    └── test_pdf_downloader.py
```

### 2.3 Backward Compatibility Strategy

**Approach: Feature Flag with Dual Implementation**

```python
# Environment variable to control PDF processing method
USE_DOCLING = os.environ.get('USE_DOCLING', 'false').lower() == 'true'

if USE_DOCLING:
    # New Docling-based processing
    from utils.pdf_processor import DoclingPDFProcessor
    processor = DoclingPDFProcessor()
else:
    # Legacy PyPDF processing (current implementation)
    from langchain_community.document_loaders import PyPDFLoader
    # ... existing code
```

**Benefits:**
- Zero-risk deployment (can toggle back instantly)
- Side-by-side comparison testing
- Gradual migration path
- Easy A/B testing

### 2.4 API Design

**Existing Endpoint (Enhanced):**
```
POST /api/load-pdf
{
  "server_name": "IBM_Power_S1014",
  "collection_name": "sales_manuals",
  "use_docling": true,              // NEW: Optional override
  "chunk_size": 512,                // NEW: Optional override
  "chunk_overlap": 50               // NEW: Optional override
}
```

**New Endpoint:**
```
POST /api/load-pdf-url
{
  "url": "https://www.ibm.com/docs/...",
  "collection_name": "ibm_docs",
  "use_docling": true,
  "chunk_size": 512,
  "chunk_overlap": 50
}
```

**Response (Enhanced):**
```json
{
  "success": true,
  "message": "Successfully loaded IBM_Power_S1014",
  "chunks": 156,
  "collection": "sales_manuals",
  "processing_method": "docling",
  "metadata": {
    "pages": 42,
    "tables": 8,
    "chapters": 5,
    "sections": 23,
    "processing_time_seconds": 45.2
  }
}
```

---

## 3. Dependencies

### 3.1 New Dependencies Required

```python
# Document Processing - Docling Stack
docling==2.0.0                    # Core Docling library
docling-core==2.0.0               # Docling core types
pypdfium2==4.30.0                 # PDF backend for Docling

# Text Processing
sentence-splitter==1.4            # Sentence boundary detection
rapidfuzz==3.6.1                  # Fuzzy string matching for TOC

# PDF Analysis
pdfplumber==0.11.0                # Font size extraction
pdfminer.six==20231228            # TOC extraction

# Utilities
tqdm==4.66.1                      # Progress bars (optional)
```

### 3.2 Version Compatibility Matrix

| Package | Current | Required | Power10 Compatible | Notes |
|---------|---------|----------|-------------------|-------|
| docling | N/A | 2.0.0 | ✅ Yes | Pure Python + pypdfium2 |
| pypdfium2 | N/A | 4.30.0 | ✅ Yes | Has ppc64le wheels |
| sentence-splitter | N/A | 1.4 | ✅ Yes | Pure Python |
| rapidfuzz | N/A | 3.6.1 | ✅ Yes | Has ppc64le wheels |
| pdfplumber | N/A | 0.11.0 | ✅ Yes | Pure Python |
| pdfminer.six | N/A | 20231228 | ✅ Yes | Pure Python |

### 3.3 Docker Image Size Impact

**Current Image Size:** ~2.5 GB (estimated)

**Additional Size from New Dependencies:**
- Docling + docling-core: ~50 MB
- pypdfium2: ~30 MB
- sentence-splitter: ~5 MB
- rapidfuzz: ~2 MB
- pdfplumber + pdfminer.six: ~10 MB

**Estimated New Image Size:** ~2.6 GB (+100 MB, ~4% increase)

---

*Continued in next section...*
## 4. Code Changes Required

### 4.1 Summary of Changes

| File | Type | Lines Changed | Complexity |
|------|------|---------------|------------|
| `app.py` | Modify | ~150 | Medium |
| `requirements.txt` | Modify | +10 | Low |
| `Dockerfile` | Modify | ~20 | Low |
| `utils/docling_converter.py` | New | ~300 | High |
| `utils/hierarchical_chunker.py` | New | ~400 | High |
| `utils/table_processor.py` | New | ~200 | Medium |
| `utils/token_utils.py` | New | ~150 | Medium |
| `utils/pdf_downloader.py` | New | ~150 | Medium |
| `utils/pdf_processor.py` | New | ~250 | Medium |
| `config/docling_config.py` | New | ~100 | Low |

**Total New Code:** ~1,550 lines  
**Total Modified Code:** ~180 lines

### 4.2 Key Implementation Details

#### 4.2.1 Docling Converter (`utils/docling_converter.py`)

**Core Functionality:**
- Wrap Docling DocumentConverter with retry logic
- Handle large PDFs by chunking (100 pages per chunk)
- Extract table of contents (TOC) from PDF metadata
- Cache conversion results

**Key Methods:**
```python
def convert_pdf(pdf_path: Path) -> DoclingDocument:
    """Convert PDF with automatic chunking for large files"""
    
def extract_toc(pdf_path: Path) -> Dict[str, int]:
    """Extract TOC with header levels"""
    
def get_page_count(pdf_path: Path) -> int:
    """Get total page count"""
```

**Adapted From:** spyre-rag `pdf_utils.py` lines 185-299

#### 4.2.2 Hierarchical Chunker (`utils/hierarchical_chunker.py`)

**Core Functionality:**
- Detect headers using markdown syntax or font size
- Build hierarchical structure (chapter → section → subsection)
- Split content by tokens with overlap
- Preserve metadata at each level

**Key Methods:**
```python
def chunk_document(docling_doc: DoclingDocument) -> List[Dict]:
    """Create hierarchical chunks"""
    
def _detect_header_level(text: str, font_size: float) -> Tuple[int, str]:
    """Determine header level from text or font"""
    
def _split_by_tokens(text: str, max_tokens: int, overlap: int) -> List[str]:
    """Token-aware text splitting"""
```

**Adapted From:** spyre-rag `doc_utils.py` lines 497-693

#### 4.2.3 Table Processor (`utils/table_processor.py`)

**Core Functionality:**
- Extract tables from DoclingDocument
- Preserve HTML structure
- Extract captions
- Optional LLM summarization

**Key Methods:**
```python
def extract_tables(docling_doc: DoclingDocument) -> List[Dict]:
    """Extract all tables with metadata"""
    
def summarize_table(table_html: str) -> str:
    """Generate table summary using LLM (optional)"""
```

**Adapted From:** spyre-rag `doc_utils.py` lines 135-170

#### 4.2.4 Token Utils (`utils/token_utils.py`)

**Core Functionality:**
- Count tokens using HuggingFace tokenizer
- Split text by token count with overlap
- Sentence boundary detection

**Key Methods:**
```python
def count_tokens(text: str, model: str = "all-MiniLM-L6-v2") -> int:
    """Count tokens in text"""
    
def split_text_by_tokens(text: str, max_tokens: int, overlap: int) -> List[str]:
    """Split text maintaining token limits"""
```

**Adapted From:** spyre-rag `doc_utils.py` lines 530-564

#### 4.2.5 PDF Downloader (`utils/pdf_downloader.py`)

**Core Functionality:**
- Download PDFs from URLs
- Validate URLs and content type
- Cache downloaded files
- Handle network errors

**Key Methods:**
```python
def download_pdf(url: str) -> Path:
    """Download and cache PDF from URL"""
    
def validate_url(url: str) -> bool:
    """Check if URL is valid and accessible"""
```

**New Implementation** (not in spyre-rag)

---

## 5. Implementation Steps

### Phase 1: Foundation (Week 1)

#### Step 1.1: Setup Development Environment
**Duration:** 1 day  
**Effort:** 4 hours

**Tasks:**
1. Create feature branch: `feature/docling-integration`
2. Install dependencies locally
3. Verify Docling functionality
4. Create directory structure

**Testing:**
```bash
python -c "from docling.document_converter import DocumentConverter; print('OK')"
```

**Success Criteria:**
- ✅ All dependencies install
- ✅ Docling converts test PDF
- ✅ Directory structure created

#### Step 1.2: Implement Configuration Module
**Duration:** 0.5 days  
**Effort:** 4 hours

**Tasks:**
1. Create `config/docling_config.py`
2. Implement DoclingConfig dataclass
3. Add environment variable loading
4. Add validation

**Success Criteria:**
- ✅ Config loads from environment
- ✅ Defaults work
- ✅ Validation catches errors

#### Step 1.3: Implement Token Utilities
**Duration:** 1 day  
**Effort:** 6 hours

**Tasks:**
1. Create `utils/token_utils.py`
2. Implement token counting
3. Implement token-based splitting
4. Add unit tests

**Success Criteria:**
- ✅ Token counting accurate
- ✅ Splitting respects limits
- ✅ Overlap works
- ✅ Tests pass

### Phase 2: Core Docling Integration (Week 2)

#### Step 2.1: Implement Docling Converter
**Duration:** 2 days  
**Effort:** 12 hours

**Tasks:**
1. Create `utils/docling_converter.py`
2. Implement conversion with chunking
3. Add retry logic
4. Add TOC extraction
5. Add unit tests

**Success Criteria:**
- ✅ Converts small PDFs
- ✅ Handles large PDFs
- ✅ Extracts TOC
- ✅ Retry works
- ✅ Tests pass

#### Step 2.2: Implement Table Processor
**Duration:** 1.5 days  
**Effort:** 10 hours

**Tasks:**
1. Create `utils/table_processor.py`
2. Implement table extraction
3. Add HTML preservation
4. Add optional summarization
5. Add unit tests

**Success Criteria:**
- ✅ Extracts tables
- ✅ Preserves HTML
- ✅ Summarization works
- ✅ Tests pass

#### Step 2.3: Implement Hierarchical Chunker
**Duration:** 2.5 days  
**Effort:** 16 hours

**Tasks:**
1. Create `utils/hierarchical_chunker.py`
2. Implement header detection
3. Implement hierarchy tracking
4. Implement token-based splitting
5. Add metadata enrichment
6. Add comprehensive tests

**Success Criteria:**
- ✅ Detects headers
- ✅ Preserves hierarchy
- ✅ Respects token limits
- ✅ Overlap works
- ✅ Tests pass

### Phase 3: Integration & API (Week 3)

#### Step 3.1: Implement PDF Processor
**Duration:** 1.5 days  
**Effort:** 10 hours

**Tasks:**
1. Create `utils/pdf_processor.py`
2. Orchestrate pipeline
3. Add error handling
4. Add integration tests

**Success Criteria:**
- ✅ End-to-end works
- ✅ Error handling robust
- ✅ Tests pass

#### Step 3.2: Implement PDF Downloader
**Duration:** 1 day  
**Effort:** 6 hours

**Tasks:**
1. Create `utils/pdf_downloader.py`
2. Implement download with caching
3. Add URL validation
4. Add unit tests

**Success Criteria:**
- ✅ Downloads work
- ✅ Caching works
- ✅ Validation works
- ✅ Tests pass

#### Step 3.3: Modify Flask API
**Duration:** 2 days  
**Effort:** 12 hours

**Tasks:**
1. Modify `app.py`
2. Add feature flag
3. Add new endpoint
4. Update documentation
5. Add API tests

**Success Criteria:**
- ✅ Legacy mode works
- ✅ Docling mode works
- ✅ URL loading works
- ✅ Tests pass

### Phase 4: Testing & Validation (Week 4)

#### Step 4.1: Comparison Testing
**Duration:** 2 days  
**Effort:** 12 hours

**Tasks:**
1. Create comparison suite
2. Process PDFs both ways
3. Compare results
4. Document findings
5. Create benchmarks

**Success Criteria:**
- ✅ Docling more structured
- ✅ Tables extracted
- ✅ Hierarchy preserved
- ✅ Performance acceptable

#### Step 4.2: Integration Testing
**Duration:** 2 days  
**Effort:** 12 hours

**Tasks:**
1. Test with real PDFs
2. Test various PDF types
3. Test error scenarios
4. Test large PDFs
5. Test retrieval quality

**Success Criteria:**
- ✅ All tests pass
- ✅ Real PDFs work
- ✅ Errors handled
- ✅ Large PDFs work
- ✅ Quality improved

#### Step 4.3: Performance Testing
**Duration:** 1 day  
**Effort:** 6 hours

**Tasks:**
1. Benchmark processing
2. Measure memory
3. Test concurrency
4. Identify bottlenecks
5. Optimize if needed

**Success Criteria:**
- ✅ Time acceptable
- ✅ Memory reasonable
- ✅ No leaks
- ✅ Concurrency works

### Phase 5: Deployment (Week 5)

#### Step 5.1: Update Docker Build
**Duration:** 1 day  
**Effort:** 6 hours

**Tasks:**
1. Update Dockerfile
2. Test build on Power10
3. Verify image size
4. Test container

**Success Criteria:**
- ✅ Build succeeds
- ✅ Size acceptable
- ✅ Container starts
- ✅ Health check passes

#### Step 5.2: Update OpenShift Deployment
**Duration:** 1 day  
**Effort:** 6 hours

**Tasks:**
1. Update deployment YAML
2. Add PVC for cache
3. Deploy to dev
4. Test deployment

**Success Criteria:**
- ✅ Deployment succeeds
- ✅ Pod starts
- ✅ Health check passes
- ✅ API accessible

#### Step 5.3: Documentation & Rollout
**Duration:** 1 day  
**Effort:** 6 hours

**Tasks:**
1. Update README
2. Create migration guide
3. Update API docs
4. Create config guide
5. Plan rollout

**Success Criteria:**
- ✅ Documentation complete
- ✅ Migration guide clear
- ✅ Rollout planned

**Total Effort:** ~130 hours (~3.25 weeks)

---

## 6. Configuration

### 6.1 Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `USE_DOCLING` | `false` | Enable Docling processing |
| `DOCLING_CHUNK_SIZE` | `512` | Max tokens per chunk |
| `DOCLING_OVERLAP` | `50` | Token overlap |
| `DOCLING_MODELS_PATH` | None | Path to models (optional) |
| `PDF_CACHE_DIR` | `/app/pdf_cache` | Cache for downloaded PDFs |
| `DOCLING_EXTRACT_TABLES` | `true` | Extract tables |
| `DOCLING_SUMMARIZE_TABLES` | `false` | Summarize tables with LLM |
| `DOCLING_DO_OCR` | `false` | Enable OCR |
| `DOCLING_PDF_CHUNK_SIZE` | `100` | Pages per chunk |

### 6.2 Configuration Examples

#### Development
```bash
export USE_DOCLING=true
export DOCLING_CHUNK_SIZE=512
export DOCLING_OVERLAP=50
export PDF_CACHE_DIR=./pdf_cache
```

#### Production (OpenShift)
```yaml
env:
  - name: USE_DOCLING
    value: "true"
  - name: DOCLING_CHUNK_SIZE
    value: "512"
  - name: DOCLING_OVERLAP
    value: "50"
  - name: PDF_CACHE_DIR
    value: "/app/pdf_cache"
```

### 6.3 Model Management

**Option 1: Runtime Download (Default)**
- Models download on first use
- Cached in container
- Slower first startup (~2-3 min)

**Option 2: Pre-download in Image**
```dockerfile
RUN python -c "from docling.document_converter import DocumentConverter; DocumentConverter()"
```
- Faster startup
- Larger image (+500MB)

**Option 3: Mount from PVC (Recommended)**
```yaml
volumeMounts:
  - name: docling-models
    mountPath: /models/docling
```
- Shared across pods
- Faster startup
- One-time download

---

## 7. Testing Strategy

### 7.1 Unit Tests

**Coverage Target:** >80%

**Test Files:**
- `test_docling_converter.py` - Conversion tests
- `test_hierarchical_chunker.py` - Chunking tests
- `test_table_processor.py` - Table tests
- `test_token_utils.py` - Token tests
- `test_pdf_downloader.py` - Download tests
- `test_config.py` - Config tests

**Key Test Cases:**

1. **Docling Converter**
   - Convert small PDF
   - Convert large PDF with chunking
   - Extract TOC
   - Handle corrupted PDFs
   - Retry on errors

2. **Hierarchical Chunker**
   - Detect markdown headers
   - Detect font-based headers
   - Preserve hierarchy
   - Respect token limits
   - Apply overlap

3. **Table Processor**
   - Extract tables
   - Preserve HTML
   - Summarize tables
   - Filter irrelevant tables

4. **Token Utils**
   - Count tokens
   - Split by tokens
   - Handle edge cases

5. **PDF Downloader**
   - Download PDFs
   - Cache files
   - Validate URLs
   - Handle errors

### 7.2 Integration Tests

**Test Scenarios:**

1. **End-to-End Processing**
```python
def test_e2e_docling():
    response = client.post('/api/load-pdf', json={
        'server_name': 'IBM_Power_S1014',
        'use_docling': True
    })
    assert response.json['processing_method'] == 'docling'
    assert response.json['metadata']['tables'] > 0
```

2. **URL Loading**
```python
def test_url_loading():
    response = client.post('/api/load-pdf-url', json={
        'url': 'https://example.com/doc.pdf'
    })
    assert response.status_code == 200
```

3. **Feature Flag**
```python
def test_feature_flag():
    # Test both modes
    docling_result = load_with_docling()
    pypdf_result = load_with_pypdf()
    assert docling_result['chunks'] != pypdf_result['chunks']
```

### 7.3 Comparison Tests

**Metrics:**
- Chunk count
- Average chunk size
- Metadata richness
- Table extraction
- Structure preservation
- Processing time
- Memory usage

**Implementation:**
```python
def test_comparison():
    pypdf_result = process_with_pypdf("test.pdf")
    docling_result = process_with_docling("test.pdf")
    
    print(f"PyPDF chunks: {len(pypdf_result.chunks)}")
    print(f"Docling chunks: {len(docling_result.chunks)}")
    print(f"Docling tables: {docling_result.metadata['tables']}")
    print(f"Docling chapters: {docling_result.metadata['chapters']}")
```

### 7.4 Performance Tests

**Benchmarks:**
- Processing time per page
- Memory usage per page
- Concurrent processing
- Large PDF handling (>500 pages)

**Targets:**
- <2 minutes for 100-page PDF
- <4GB memory usage
- No memory leaks
- Support 3+ concurrent requests

---

## 8. Deployment Considerations

### 8.1 Resource Requirements

**Current Resources:**
- CPU: 2 cores
- Memory: 4GB
- Storage: 10GB

**Recommended with Docling:**
- CPU: 2-4 cores (same or +2)
- Memory: 6GB (+2GB for models)
- Storage: 15GB (+5GB for cache)

### 8.2 Dockerfile Updates

**Key Changes:**
```dockerfile
# Add new dependencies
RUN pip install docling docling-core pypdfium2 ...

# Create cache directory
RUN mkdir -p /app/pdf_cache

# Add environment variables
ENV USE_DOCLING=false \
    DOCLING_CHUNK_SIZE=512 \
    PDF_CACHE_DIR=/app/pdf_cache
```

### 8.3 OpenShift Deployment

**New PVC for PDF Cache:**
```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: rag-backend-pdf-cache
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 5Gi
```

**Updated Deployment:**
```yaml
spec:
  template:
    spec:
      containers:
      - name: rag-backend
        env:
        - name: USE_DOCLING
          value: "true"
        - name: DOCLING_CHUNK_SIZE
          value: "512"
        volumeMounts:
        - name: pdf-cache
          mountPath: /app/pdf_cache
      volumes:
      - name: pdf-cache
        persistentVolumeClaim:
          claimName: rag-backend-pdf-cache
```

### 8.4 Rollout Strategy

**Phase 1: Dev Environment (Week 5)**
- Deploy with `USE_DOCLING=false`
- Verify deployment
- Enable Docling for testing
- Validate functionality

**Phase 2: Staging (Week 6)**
- Deploy with `USE_DOCLING=true`
- Run comparison tests
- Validate performance
- Gather feedback

**Phase 3: Production (Week 7)**
- Deploy with `USE_DOCLING=false` initially
- Monitor for issues
- Gradually enable Docling
- Monitor performance and quality

**Rollback Plan:**
- Set `USE_DOCLING=false`
- Restart pods
- Verify legacy mode works
- Investigate issues

---

## 9. Risk Assessment

### 9.1 Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Docling dependencies fail on Power10 | Low | High | Test early, use IBM wheels, have fallback |
| Performance degradation | Medium | Medium | Benchmark early, optimize, use feature flag |
| Memory issues with large PDFs | Medium | High | Implement chunking, monitor memory, set limits |
| Breaking changes to API | Low | High | Maintain backward compatibility, use feature flag |
| Model download failures | Medium | Low | Pre-download models, cache in PVC |

### 9.2 Operational Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Increased resource usage | High | Medium | Monitor resources, adjust limits, scale if needed |
| Longer processing times | Medium | Medium | Set expectations, optimize, use async processing |
| Storage exhaustion | Low | Medium | Monitor storage, implement cleanup, set quotas |
| Deployment failures | Low | High | Test thoroughly, have rollback plan |

### 9.3 Mitigation Strategies

**1. Feature Flag**
- Allows instant rollback
- Enables gradual rollout
- Facilitates A/B testing

**2. Comprehensive Testing**
- Unit tests for all components
- Integration tests for workflows
- Performance tests for benchmarks
- Comparison tests for quality

**3. Monitoring**
- Track processing times
- Monitor memory usage
- Alert on errors
- Log all operations

**4. Documentation**
- Clear migration guide
- Troubleshooting guide
- Configuration examples
- API documentation

---

## 10. Success Criteria

### 10.1 Functional Requirements

✅ **Must Have:**
- Docling converts PDFs successfully
- Hierarchical chunking preserves structure
- Tables extracted and processed
- Token-based splitting with overlap
- Backward compatibility maintained
- Feature flag works correctly

✅ **Should Have:**
- Online PDF download works
- LLM table summarization (optional)
- Comprehensive error handling
- Detailed logging

✅ **Nice to Have:**
- OCR support for scanned PDFs
- Multi-language support
- Advanced table filtering

### 10.2 Performance Requirements

✅ **Processing Time:**
- <2 minutes for 100-page PDF
- <10 minutes for 500-page PDF
- Acceptable for production use

✅ **Resource Usage:**
- <6GB memory per pod
- <4 CPU cores per pod
- <15GB storage total

✅ **Quality:**
- Better structure preservation than PyPDF
- Table extraction >90% accuracy
- Chunk quality improved (subjective)

### 10.3 Acceptance Criteria

**Phase 1 Complete:**
- ✅ All unit tests pass
- ✅ Configuration module works
- ✅ Token utilities functional

**Phase 2 Complete:**
- ✅ Docling converter works
- ✅ Table processor works
- ✅ Hierarchical chunker works
- ✅ Integration tests pass

**Phase 3 Complete:**
- ✅ API endpoints work
- ✅ Feature flag works
- ✅ URL download works
- ✅ API tests pass

**Phase 4 Complete:**
- ✅ Comparison tests show improvement
- ✅ Performance acceptable
- ✅ All integration tests pass

**Phase 5 Complete:**
- ✅ Docker build succeeds
- ✅ OpenShift deployment works
- ✅ Documentation complete
- ✅ Ready for production

### 10.4 Quality Gates

**Before Merge:**
- All tests pass (>80% coverage)
- Code review approved
- Documentation updated
- Performance benchmarks met

**Before Production:**
- Staging validation complete
- Performance monitoring in place
- Rollback plan tested
- Team trained on new features

---

## Appendix A: Reference Links

**Spyre-RAG Implementation:**
- [`pdf_utils.py`](../project-ai-services/spyre-rag/src/digitize/pdf_utils.py)
- [`doc_utils.py`](../project-ai-services/spyre-rag/src/digitize/doc_utils.py)
- [`config.py`](../project-ai-services/spyre-rag/src/digitize/config.py)

**Current Implementation:**
- [`app.py`](../RAG-with-Notebook/rag-backend/app.py)
- [`requirements.txt`](../RAG-with-Notebook/rag-backend/requirements.txt)
- [`Dockerfile`](../RAG-with-Notebook/rag-backend/Dockerfile)

**Documentation:**
- Docling: https://github.com/DS4SD/docling
- pypdfium2: https://github.com/pypdfium2-team/pypdfium2

---

## Appendix B: Glossary

**Docling:** Document processing library for converting PDFs to structured formats

**Hierarchical Chunking:** Splitting documents while preserving chapter/section structure

**Token-based Splitting:** Splitting text based on token count rather than characters

**TOC:** Table of Contents extracted from PDF metadata

**Feature Flag:** Configuration option to enable/disable features

**ChromaDB:** Vector database for storing embeddings

**LangChain:** Framework for building LLM applications

---

**Document Status:** Draft  
**Last Updated:** 2026-04-22  
**Next Review:** After Phase 1 completion

---

*End of Implementation Plan*