# IBM Docs Selenium Scraper - Deployment Script (PowerShell)
# Deploys the scraper service to OpenShift

$ErrorActionPreference = "Stop"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "IBM Docs Selenium Scraper Deployment" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Check if oc is available
try {
    $null = Get-Command oc -ErrorAction Stop
} catch {
    Write-Host "Error: 'oc' command not found" -ForegroundColor Red
    Write-Host "Please install OpenShift CLI and login first" -ForegroundColor Yellow
    exit 1
}

# Check if logged in
try {
    $user = oc whoami 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Not logged in"
    }
} catch {
    Write-Host "Error: Not logged into OpenShift" -ForegroundColor Red
    Write-Host "Please run: oc login <cluster-url>" -ForegroundColor Yellow
    exit 1
}

Write-Host "Logged in as: $user" -ForegroundColor Green
$project = oc project -q
Write-Host "Current project: $project" -ForegroundColor Green
Write-Host ""

# Check if build config exists
$ErrorActionPreference = "SilentlyContinue"
oc get bc/selenium-scraper 2>&1 | Out-Null
$ErrorActionPreference = "Stop"

if ($LASTEXITCODE -eq 0) {
    Write-Host "Build config 'selenium-scraper' already exists" -ForegroundColor Yellow
    Write-Host "   Updating existing build..." -ForegroundColor Yellow
} else {
    Write-Host "Creating new build config..." -ForegroundColor Cyan
    oc new-build --name selenium-scraper --binary --strategy docker
}

Write-Host ""
Write-Host "Building container image..." -ForegroundColor Cyan
oc start-build selenium-scraper --from-dir=. --follow

if ($LASTEXITCODE -ne 0) {
    Write-Host "Build failed!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Build completed successfully" -ForegroundColor Green
Write-Host ""

# Check if deployment exists
$ErrorActionPreference = "SilentlyContinue"
oc get deployment/selenium-scraper 2>&1 | Out-Null
$ErrorActionPreference = "Stop"

if ($LASTEXITCODE -eq 0) {
    Write-Host "Deployment 'selenium-scraper' already exists" -ForegroundColor Yellow
    Write-Host "   Triggering rollout..." -ForegroundColor Yellow
    oc rollout restart deployment/selenium-scraper
    oc rollout status deployment/selenium-scraper
} else {
    Write-Host "Creating new deployment..." -ForegroundColor Cyan
    oc new-app selenium-scraper
    
    # Wait for deployment
    Write-Host "   Waiting for deployment to complete..." -ForegroundColor Cyan
    oc rollout status deployment/selenium-scraper
}

Write-Host ""

# Check if route exists
$ErrorActionPreference = "SilentlyContinue"
oc get route/selenium-scraper 2>&1 | Out-Null
$ErrorActionPreference = "Stop"

if ($LASTEXITCODE -eq 0) {
    Write-Host "Route already exists" -ForegroundColor Yellow
} else {
    Write-Host "Creating route..." -ForegroundColor Cyan
    oc expose svc/selenium-scraper
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Deployment Complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Get route URL
$route = oc get route selenium-scraper -o jsonpath='{.spec.host}'
Write-Host "Service URL: http://$route" -ForegroundColor Green
Write-Host ""

Write-Host "Available endpoints:" -ForegroundColor Cyan
Write-Host "   Health check:  http://$route/health"
Write-Host "   Test E1180:    http://$route/scrape-e1180"
Write-Host "   Scrape custom: http://$route/scrape?url=<ibm-docs-url>"
Write-Host "   Full extract:  http://$route/extract-content?url=<ibm-docs-url>"
Write-Host ""

Write-Host "Test the service (PowerShell):" -ForegroundColor Cyan
$testCmd1 = "Invoke-WebRequest -Uri `"http://$route/health`" | Select-Object -ExpandProperty Content"
$testCmd2 = "Invoke-WebRequest -Uri `"http://$route/scrape-e1180`" | Select-Object -ExpandProperty Content | ConvertFrom-Json"
Write-Host "   $testCmd1"
Write-Host "   $testCmd2"
Write-Host ""

Write-Host "View logs:" -ForegroundColor Cyan
Write-Host "   oc logs -f deployment/selenium-scraper"
Write-Host ""

Write-Host "Check status:" -ForegroundColor Cyan
Write-Host "   oc get pods -l app=selenium-scraper"
Write-Host ""

# Made with Bob