# Chromium Scraper Deployment Guide

## Overview
This scraper uses **ungoogled-chromium** (v84) and **ChromeDriver** from EPEL to scrape JavaScript-rendered IBM Docs pages on ppc64le architecture.

## Architecture Solution
After extensive testing, we found that:
- **Firefox**: Not available in EPEL for ppc64le
- **pyppeteer**: Downloads x86_64 Chromium binaries (architecture mismatch)
- **Simple scraper**: No JavaScript rendering (0% quality score)
- **✅ ungoogled-chromium + ChromeDriver**: Working solution for ppc64le

## Package Sources
- **ungoogled-chromium-browser-stable**: From chromium-ppc64le repository (v84.0.4147.125)
- **chromedriver**: From EPEL repository (compatible with Chromium v84)

## Files Updated

### 1. Dockerfile
```dockerfile
# Install ungoogled-chromium and chromedriver from EPEL
# Skip broken dependencies for GUI features we don't need in headless mode
RUN dnf install -y ungoogled-chromium-browser-stable chromedriver --skip-broken --nobest && dnf clean all

# Verify installation
RUN which chromium-browser && which chromedriver && chromium-browser --version && chromedriver --version
```

**Key changes:**
- Changed from `chromium-browser-stable` to `ungoogled-chromium-browser-stable`
- Added `chromedriver` package from EPEL
- Updated verification to check both binaries and their versions

### 2. chromium_scraper.py
```python
def create_driver():
    """Create a headless Chromium WebDriver using ppc64le community build"""
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-software-rasterizer')
    options.add_argument('--disable-extensions')
    # ungoogled-chromium-browser binary location
    options.binary_location = '/usr/bin/chromium-browser'
    
    # ChromeDriver from EPEL
    service = Service('/usr/bin/chromedriver')
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(60)
    
    return driver
```

**Key changes:**
- Binary location: `/usr/bin/chromium-browser` (ungoogled-chromium)
- ChromeDriver location: `/usr/bin/chromedriver` (from EPEL)
- Updated version info to reflect ungoogled-chromium v84

## Deployment Steps

### 1. Navigate to scraper directory
```powershell
cd C:\Users\029878866\EMEA-AI-SQUAD\RAG-with-Notebook\Part3-RAG-Sales-Manual\scraper-test
```

### 2. Deploy using PowerShell script
```powershell
.\deploy.ps1
```

This will:
- Delete existing deployment and service
- Build new container image with ungoogled-chromium
- Create deployment and service
- Expose route
- Show pod status and logs

### 3. Verify installation
Once the pod is running, check that both binaries are installed:
```powershell
# Get pod name
oc get pods | Select-String "selenium-scraper"

# Check binaries (replace POD_NAME)
oc exec POD_NAME -- which chromium-browser
oc exec POD_NAME -- which chromedriver
oc exec POD_NAME -- chromium-browser --version
oc exec POD_NAME -- chromedriver --version
```

Expected output:
```
/usr/bin/chromium-browser
/usr/bin/chromedriver
Chromium 84.0.4147.125
ChromeDriver 84.0.4147.30
```

### 4. Test the scraper
```powershell
# Get the route URL
$ROUTE = oc get route selenium-scraper -o jsonpath='{.spec.host}'

# Test health endpoint
curl "http://$ROUTE/health"

# Test E1180 scraping
curl "http://$ROUTE/scrape-e1180"
```

## API Endpoints

### Health Check
```
GET /health
```
Returns service status and Chromium version info.

### Scrape E1180 Sales Manual (Test)
```
GET /scrape-e1180?wait=10
```
Scrapes the IBM Power E1180 Sales Manual as a test.

### Scrape Custom URL
```
GET /scrape?url=<IBM_DOCS_URL>&wait=10
```
Scrapes any IBM Docs page.

### Extract Full Content
```
GET /extract-content?url=<IBM_DOCS_URL>
```
Extracts complete structured content with all sections.

## Quality Score
The scraper calculates a quality score based on:
- **Paragraphs**: >10 paragraphs
- **Headings**: >5 headings (h2, h3)
- **Tables**: At least 1 table
- **Lists**: At least 1 list (ul/ol)
- **Content length**: >5000 characters

**Score interpretation:**
- **≥80%**: Excellent - Ready for RAG processing
- **60-79%**: Good - Usable with minor adjustments
- **<60%**: Poor - May need additional processing

## Troubleshooting

### Pod fails to start
Check build logs:
```powershell
oc logs -f bc/selenium-scraper
```

### Chromium not found
Verify installation in running pod:
```powershell
oc exec POD_NAME -- rpm -qa | Select-String "chromium"
oc exec POD_NAME -- rpm -qa | Select-String "chromedriver"
```

### Scraping returns 0% quality
This means JavaScript didn't render. Check:
1. Wait time (increase `?wait=15` parameter)
2. Pod logs for Selenium errors
3. Chromium/ChromeDriver compatibility

### Version mismatch errors
Chromium v84 and ChromeDriver must be compatible. If you see version errors:
```powershell
oc exec POD_NAME -- chromium-browser --version
oc exec POD_NAME -- chromedriver --version
```

## Next Steps
1. ✅ Deploy updated scraper
2. ✅ Test E1180 scraping with quality score >80%
3. Create `/ibm-power-rag` UI page
4. Integrate scraper with RAG backend
5. Implement change detection for sales manuals

## References
- Chromium ppc64le: https://gitlab.com/chromium-ppc64le/chromium-ppc64le
- EPEL Repository: https://fedoraproject.org/wiki/EPEL
- Selenium Documentation: https://selenium-python.readthedocs.io/