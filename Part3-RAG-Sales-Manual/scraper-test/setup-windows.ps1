# Windows Scraper Setup Script
# Automates installation and testing

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "  IBM Docs Scraper - Windows Setup" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""

# Check Python
Write-Host "[1/5] Checking Python installation..." -ForegroundColor Yellow
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if ($null -eq $pythonCmd) {
    $pythonCmd = Get-Command python3 -ErrorAction SilentlyContinue
}

if ($null -eq $pythonCmd) {
    Write-Host "  X Python not found!" -ForegroundColor Red
    Write-Host "  Please install Python 3.9+ from https://www.python.org/downloads/" -ForegroundColor Red
    Write-Host "  Or check if Python is in your PATH" -ForegroundColor Red
    exit 1
}

$pythonVersion = & $pythonCmd.Source --version 2>&1
Write-Host "  OK Found: $pythonVersion" -ForegroundColor Green

# Check Chrome
Write-Host "[2/5] Checking Google Chrome..." -ForegroundColor Yellow
$chromePaths = @(
    "C:\Program Files\Google\Chrome\Application\chrome.exe",
    "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    "$env:LOCALAPPDATA\Google\Chrome\Application\chrome.exe"
)

$chromeFound = $false
foreach ($path in $chromePaths) {
    if (Test-Path $path) {
        Write-Host "  OK Found Chrome at: $path" -ForegroundColor Green
        $chromeFound = $true
        break
    }
}

if (-not $chromeFound) {
    Write-Host "  X Google Chrome not found!" -ForegroundColor Red
    Write-Host "  Please install Chrome from https://www.google.com/chrome/" -ForegroundColor Red
    exit 1
}

# Create virtual environment
Write-Host "[3/5] Creating Python virtual environment..." -ForegroundColor Yellow
if (Test-Path "venv") {
    Write-Host "  OK Virtual environment already exists" -ForegroundColor Green
} else {
    & $pythonCmd.Source -m venv venv
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  OK Virtual environment created" -ForegroundColor Green
    } else {
        Write-Host "  X Failed to create virtual environment" -ForegroundColor Red
        exit 1
    }
}

# Activate virtual environment and install dependencies
Write-Host "[4/5] Installing dependencies..." -ForegroundColor Yellow
$activateScript = ".\venv\Scripts\Activate.ps1"
if (Test-Path $activateScript) {
    & $activateScript
    pip install -q -r requirements-windows.txt
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  OK Dependencies installed successfully" -ForegroundColor Green
    } else {
        Write-Host "  X Failed to install dependencies" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "  X Virtual environment activation script not found" -ForegroundColor Red
    exit 1
}

# Test scraper
Write-Host "[5/5] Testing scraper..." -ForegroundColor Yellow
$testOutput = python windows_scraper.py 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "  OK Scraper is ready to use" -ForegroundColor Green
} else {
    Write-Host "  X Scraper test failed" -ForegroundColor Red
    Write-Host "  Error: $testOutput" -ForegroundColor Red
}

Write-Host ""
Write-Host "================================================================================" -ForegroundColor Green
Write-Host "  Setup Complete!" -ForegroundColor Green
Write-Host "================================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Test scraping:" -ForegroundColor White
Write-Host '     python windows_scraper.py "https://www.ibm.com/docs/en/announcements/family-908005-power-e1180-enterprise-server-9080-heu" --output test.json' -ForegroundColor Gray
Write-Host ""
Write-Host "  2. Get backend URL:" -ForegroundColor White
Write-Host '     oc get route rag-backend -o jsonpath="{.spec.host}"' -ForegroundColor Gray
Write-Host ""
Write-Host "  3. Scrape and send to backend:" -ForegroundColor White
Write-Host '     python windows_scraper.py "URL" --backend http://BACKEND_URL' -ForegroundColor Gray
Write-Host ""
Write-Host "For more information, see WINDOWS_SETUP.md" -ForegroundColor Cyan
Write-Host ""

# Made with Bob
