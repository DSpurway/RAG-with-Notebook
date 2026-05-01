# Windows Scraper Setup Guide

## Overview
This scraper runs on your Windows laptop (x86_64) and can send scraped content to the IBM Power backend for RAG processing. This hybrid approach solves the browser automation challenges on ppc64le architecture.

## Architecture
```
Windows Laptop (x86_64)          IBM Power Cluster (ppc64le)
┌─────────────────────┐          ┌──────────────────────┐
│  Chrome Browser     │          │   RAG Backend        │
│  + ChromeDriver     │          │   - OpenSearch       │
│  + Selenium         │  HTTP    │   - Embeddings       │
│                     │ ──────>  │   - LLM              │
│  windows_scraper.py │          │   - Vector Search    │
└─────────────────────┘          └──────────────────────┘
```

## Prerequisites

### 1. Python 3.9+
Check if installed:
```powershell
python --version
```

If not installed, download from: https://www.python.org/downloads/

### 2. Google Chrome
The scraper uses Chrome (not Edge or Firefox). Download from: https://www.google.com/chrome/

### 3. Git (optional, for cloning)
Download from: https://git-scm.com/download/win

## Installation

### Step 1: Navigate to scraper directory
```powershell
cd C:\Users\029878866\EMEA-AI-SQUAD\RAG-with-Notebook\Part3-RAG-Sales-Manual\scraper-test
```

### Step 2: Create Python virtual environment (recommended)
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

If you get an execution policy error:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\venv\Scripts\Activate.ps1
```

### Step 3: Install dependencies
```powershell
pip install -r requirements-windows.txt
```

This installs:
- **selenium**: Browser automation
- **beautifulsoup4**: HTML parsing
- **requests**: HTTP client for backend communication
- **webdriver-manager**: Auto-downloads correct ChromeDriver version
- **lxml**: Fast XML/HTML parser

### Step 4: Verify installation
```powershell
python windows_scraper.py
```

You should see usage instructions.

## Usage

### Basic Scraping (Save to File)
```powershell
# Scrape E1180 Sales Manual and save to JSON
python windows_scraper.py "https://www.ibm.com/docs/en/announcements/family-908005-power-e1180-enterprise-server-9080-heu" --output e1180.json
```

### Scrape with Custom Wait Time
```powershell
# Wait 15 seconds for JavaScript to render
python windows_scraper.py "https://www.ibm.com/docs/en/announcements/..." --wait 15 --output output.json
```

### Scrape and Send to Backend
```powershell
# Get backend route URL first
oc get route rag-backend -o jsonpath='{.spec.host}'

# Scrape and send to backend
python windows_scraper.py "https://www.ibm.com/docs/en/announcements/..." --backend http://rag-backend-route.apps.cluster.com
```

### Scrape, Save, and Send
```powershell
# Do both: save locally AND send to backend
python windows_scraper.py "https://www.ibm.com/docs/en/announcements/..." --output e1180.json --backend http://rag-backend-route.apps.cluster.com
```

## Command-Line Arguments

| Argument | Required | Description | Example |
|----------|----------|-------------|---------|
| `url` | Yes | IBM Docs URL to scrape | `"https://www.ibm.com/docs/..."` |
| `--wait` | No | Wait time for JavaScript (seconds) | `--wait 15` |
| `--output` | No | Save to JSON file | `--output e1180.json` |
| `--backend` | No | Send to backend URL | `--backend http://...` |

## Output Format

The scraper produces JSON with:
```json
{
  "success": true,
  "method": "Selenium + Chrome (Windows x86_64)",
  "url": "https://www.ibm.com/docs/...",
  "scraped_at": "2024-04-29T12:00:00",
  "page_title": "IBM Power E1180 Server",
  "stats": {
    "paragraphs": 45,
    "headings": 12,
    "tables": 3,
    "lists": 8,
    "sections": 12,
    "total_text_length": 15234
  },
  "quality_score": {
    "score": 100,
    "recommendation": "Excellent - Ready for RAG processing"
  },
  "sections": [...],
  "full_text": "..."
}
```

## Quality Score

The scraper evaluates content quality:

| Score | Rating | Meaning |
|-------|--------|---------|
| ≥80% | Excellent | Ready for RAG processing |
| 60-79% | Good | Usable with minor adjustments |
| <60% | Poor | May need additional processing |

Quality checks:
- ✅ Has >10 paragraphs
- ✅ Has >5 headings
- ✅ Has at least 1 table
- ✅ Has at least 1 list
- ✅ Has >5000 characters of content

## Troubleshooting

### Chrome/ChromeDriver version mismatch
The `webdriver-manager` package automatically downloads the correct ChromeDriver version for your Chrome browser. If you see version errors:
```powershell
# Update Chrome to latest version
# Then reinstall webdriver-manager
pip install --upgrade webdriver-manager
```

### Selenium not found
```powershell
pip install --upgrade selenium
```

### "No module named 'bs4'"
```powershell
pip install beautifulsoup4
```

### Execution policy error (PowerShell)
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Chrome not found
Make sure Google Chrome is installed (not just Edge). Download from: https://www.google.com/chrome/

### Slow scraping
Increase wait time:
```powershell
python windows_scraper.py "URL" --wait 20
```

## Backend Integration

### Step 1: Get backend route
```powershell
oc get route rag-backend -o jsonpath='{.spec.host}'
```

### Step 2: Test backend health
```powershell
$BACKEND = "http://rag-backend-route.apps.cluster.com"
curl "$BACKEND/health"
```

### Step 3: Scrape and send
```powershell
python windows_scraper.py "https://www.ibm.com/docs/..." --backend $BACKEND
```

The backend should have an endpoint `/ingest-scraped-content` that accepts POST requests with the scraped JSON data.

## Batch Scraping

Create a PowerShell script to scrape multiple pages:

```powershell
# scrape-all.ps1
$urls = @(
    "https://www.ibm.com/docs/en/announcements/family-908005-power-e1180-enterprise-server-9080-heu",
    "https://www.ibm.com/docs/en/announcements/...",
    "https://www.ibm.com/docs/en/announcements/..."
)

$backend = "http://rag-backend-route.apps.cluster.com"

foreach ($url in $urls) {
    Write-Host "Scraping: $url"
    python windows_scraper.py $url --backend $backend --output "scraped_$(Get-Date -Format 'yyyyMMdd_HHmmss').json"
    Start-Sleep -Seconds 5  # Be nice to IBM's servers
}
```

Run it:
```powershell
.\scrape-all.ps1
```

## Scheduled Scraping (Change Detection)

Use Windows Task Scheduler to run the scraper periodically:

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger (e.g., daily at 2 AM)
4. Action: Start a program
   - Program: `C:\Users\029878866\EMEA-AI-SQUAD\RAG-with-Notebook\Part3-RAG-Sales-Manual\scraper-test\venv\Scripts\python.exe`
   - Arguments: `windows_scraper.py "URL" --backend http://...`
   - Start in: `C:\Users\029878866\EMEA-AI-SQUAD\RAG-with-Notebook\Part3-RAG-Sales-Manual\scraper-test`

## Next Steps

1. ✅ Install dependencies
2. ✅ Test scraping E1180 Sales Manual
3. ✅ Verify quality score >80%
4. Create backend endpoint `/ingest-scraped-content`
5. Test end-to-end: scrape → send → RAG processing
6. Set up scheduled scraping for change detection

## Support

If you encounter issues:
1. Check Chrome and ChromeDriver versions match
2. Verify Python dependencies are installed
3. Test with simple URL first
4. Check backend is accessible from your laptop
5. Review scraper output for error messages