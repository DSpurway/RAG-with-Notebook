# Start Windows Scraper Service
# This script starts the Flask scraper service on port 5000

Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 79) -ForegroundColor Cyan
Write-Host "Starting Windows Scraper Service" -ForegroundColor Green
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 79) -ForegroundColor Cyan
Write-Host ""

# Navigate to scraper directory
$ScraperDir = "C:\Users\029878866\EMEA-AI-SQUAD\RAG-with-Notebook\Part3-RAG-Sales-Manual\scraper-test"
Set-Location $ScraperDir

# Check if virtual environment exists
if (-not (Test-Path ".\venv\Scripts\Activate.ps1")) {
    Write-Host "❌ Virtual environment not found!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please run setup first:" -ForegroundColor Yellow
    Write-Host "  1. python -m venv venv" -ForegroundColor White
    Write-Host "  2. .\venv\Scripts\Activate.ps1" -ForegroundColor White
    Write-Host "  3. pip install -r requirements-windows.txt" -ForegroundColor White
    Write-Host ""
    exit 1
}

# Activate virtual environment
Write-Host "📦 Activating virtual environment..." -ForegroundColor Cyan
& ".\venv\Scripts\Activate.ps1"

# Check if dependencies are installed
Write-Host "🔍 Checking dependencies..." -ForegroundColor Cyan
$packages = @("selenium", "beautifulsoup4", "flask", "webdriver-manager")
$missing = @()

foreach ($package in $packages) {
    $installed = pip list 2>$null | Select-String -Pattern "^$package\s"
    if (-not $installed) {
        $missing += $package
    }
}

if ($missing.Count -gt 0) {
    Write-Host "❌ Missing dependencies: $($missing -join ', ')" -ForegroundColor Red
    Write-Host ""
    Write-Host "Installing missing dependencies..." -ForegroundColor Yellow
    pip install -r requirements-windows.txt
    Write-Host ""
}

# Check if Chrome is installed
Write-Host "🌐 Checking for Google Chrome..." -ForegroundColor Cyan
$chromePaths = @(
    "${env:ProgramFiles}\Google\Chrome\Application\chrome.exe",
    "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe",
    "${env:LOCALAPPDATA}\Google\Chrome\Application\chrome.exe"
)

$chromeFound = $false
foreach ($path in $chromePaths) {
    if (Test-Path $path) {
        $chromeFound = $true
        Write-Host "   ✅ Chrome found: $path" -ForegroundColor Green
        break
    }
}

if (-not $chromeFound) {
    Write-Host "   ⚠️  Chrome not found in standard locations" -ForegroundColor Yellow
    Write-Host "   Please install Chrome from: https://www.google.com/chrome/" -ForegroundColor Yellow
    Write-Host ""
}

Write-Host ""
Write-Host "🚀 Starting scraper service on port 5000..." -ForegroundColor Green
Write-Host ""
Write-Host "Service will be available at:" -ForegroundColor Cyan
Write-Host "  - http://localhost:5000" -ForegroundColor White
Write-Host "  - http://127.0.0.1:5000" -ForegroundColor White
Write-Host ""
Write-Host "Endpoints:" -ForegroundColor Cyan
Write-Host "  - GET /health - Health check" -ForegroundColor White
Write-Host "  - GET /scrape?url=... - Scrape IBM Docs page" -ForegroundColor White
Write-Host "  - GET /scrape-e1180 - Example: Scrape E1180" -ForegroundColor White
Write-Host ""
Write-Host "Press Ctrl+C to stop the service" -ForegroundColor Yellow
Write-Host ""
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 79) -ForegroundColor Cyan
Write-Host ""

# Start the service
python windows_scraper_service.py

# Made with Bob
