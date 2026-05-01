# IBM Power Server Documentation Scraper & RAG Ingestion

This directory contains tools for scraping IBM Power server Sales Manual pages and ingesting them into the RAG (Retrieval Augmented Generation) system running on IBM Power.

## Architecture

```
Windows Laptop (x86_64)              IBM Power Cluster (ppc64le)
┌──────────────────┐                ┌────────────────────────┐
│ Web Scraper      │   HTTPS        │ RAG Backend            │
│ - Selenium       │ ─────────>     │ - Flask API            │
│ - ChromeDriver   │                │ - OpenSearch           │
│ - Python 3.x     │                │ - Granite LLM          │
└──────────────────┘                └────────────────────────┘
```

**Why Hybrid?** Browser automation tools (Selenium, ChromeDriver) don't work on IBM Power (ppc64le) architecture. Solution: scrape on Windows x86_64, send data to Power backend via HTTPS.

## Files

- **`windows_scraper.py`** - Main scraper using Selenium + Chrome
- **`ibm-power-servers.json`** - Configuration of IBM Power servers and their Sales Manual URLs
- **`ingest-all-servers.ps1`** - Batch script to ingest multiple servers
- **`test-backend-integration.ps1`** - Test script for backend integration
- **`e1180.json`** - Example scraped data (E1180 Sales Manual, 439 sections)

## Setup

### Prerequisites

1. **Python 3.x** with pip
2. **Chrome browser** installed
3. **PowerShell** (Windows)

### Install Dependencies

```powershell
pip install selenium webdriver-manager beautifulsoup4 requests
```

The scraper will automatically download the correct ChromeDriver version on first run.

## Usage

### Single Server Ingestion

Scrape and ingest a specific IBM Docs page:

```powershell
python windows_scraper.py "https://www.ibm.com/docs/en/announcements/..." --backend https://rag-backend-llm-on-techzone.apps.p1219.cecc.ihost.com
```

### Batch Ingestion

Ingest all servers from configuration:

```powershell
# Ingest all servers
.\ingest-all-servers.ps1

# Ingest specific server
.\ingest-all-servers.ps1 -ServerModel E1180

# Skip already indexed servers
.\ingest-all-servers.ps1 -SkipIndexed
```

### Test with Existing Data

Test backend integration with pre-scraped E1180 data:

```powershell
.\test-backend-integration.ps1
```

## Server Configuration

Edit `ibm-power-servers.json` to add/modify servers:

```json
{
  "model": "E1180",
  "name": "IBM Power E1180 Enterprise server",
  "processor": "POWER11",
  "url": "https://www.ibm.com/docs/en/announcements/...",
  "status": "indexed"
}
```

### Current Servers

| Model | Processor | Status | Description |
|-------|-----------|--------|-------------|
| E1080 | POWER10 | Not indexed | High-end enterprise server |
| E1050 | POWER10 | Not indexed | Mid-range enterprise server |
| S1024 | POWER10 | Not indexed | Scale-out for cloud/AI |
| S1022 | POWER10 | Not indexed | Entry-level scale-out |
| **E1180** | **POWER11** | **✅ Indexed** | Next-gen enterprise server |
| E1150 | POWER11 | Not indexed | Mid-range with POWER11 |
| S1124 | POWER11 | Not indexed | Scale-out with POWER11 |
| S1122 | POWER11 | Not indexed | Entry-level with POWER11 |

## Backend API

### Endpoints

**Ingest Scraped Content:**
```bash
POST /ingest-scraped-content
Content-Type: application/json

{
  "url": "https://www.ibm.com/docs/...",
  "title": "Server Name",
  "sections": [...],
  "collection_name": "ibm_docs"
}
```

**Query RAG System:**
```bash
POST /api/generate
Content-Type: application/json

{
  "collection_name": "ibm_docs",
  "prompt": "What are the features of E1180?",
  "top_k": 3
}
```

**List Collections:**
```bash
GET /api/collections
```

## Quality Scoring

The scraper calculates a quality score for scraped content:

- **100%** = RAG-ready (structured headings, paragraphs, lists)
- **75-99%** = Good (some structure, may need review)
- **50-74%** = Fair (limited structure)
- **<50%** = Poor (mostly unstructured text)

Target: 100% quality for optimal RAG performance.

## Troubleshooting

### ChromeDriver Issues

If ChromeDriver fails to download:
1. Check internet connection
2. Manually download from: https://chromedriver.chromium.org/
3. Place in PATH or same directory as script

### Backend Connection Issues

- **504 Gateway Timeout**: Normal for large ingestions (takes 5-10 minutes). Check backend logs to confirm success.
- **SSL Certificate Errors**: Backend uses self-signed cert. Script handles this automatically.

### Scraping Issues

- **Empty sections**: Page may use different HTML structure. Check browser console for JavaScript errors.
- **Low quality score**: Page may be poorly structured. Manual review recommended.

## Current Status

- ✅ E1180 indexed (418 documents)
- ✅ RAG queries working
- ✅ Granite LLM responding
- 🔄 7 more servers ready to index

## Next Steps

1. Run batch ingestion for remaining servers
2. Test queries across multiple server models
3. Fine-tune retrieval parameters (top_k, similarity threshold)
4. Improve answer quality (prompt engineering)

## Carbon UI

Query the indexed documentation via the Carbon UI:

```
C:\Users\029878866\EMEA-AI-SQUAD\RAG-with-Notebook\Part3-RAG-Sales-Manual\carbon-rag-ui
```

## Notes

- Scraping respects IBM's robots.txt
- 5-second delay between batch requests
- All data stored in OpenSearch on IBM Power cluster
- Collection name: `ibm_docs`