# Deploy IBM Docs Scraper to IBM Cloud Code Engine

param(
    [string]$ProjectName = "scraper-service",
    [string]$AppName = "ibm-docs-scraper",
    [string]$Region = "eu-gb",  # London/UK region
    [string]$ResourceGroup = ""  # Will prompt if not provided
)

Write-Host "================================================================================"
Write-Host "Deploying IBM Docs Scraper to IBM Cloud Code Engine"
Write-Host "================================================================================"
Write-Host ""

# Check if IBM Cloud CLI is installed
Write-Host "Checking IBM Cloud CLI..." -ForegroundColor Cyan
$ibmcloudVersion = ibmcloud version 2>$null
if (-not $ibmcloudVersion) {
    Write-Host "  IBM Cloud CLI is not installed!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install it from:" -ForegroundColor Yellow
    Write-Host "  https://cloud.ibm.com/docs/cli?topic=cli-install-ibmcloud-cli" -ForegroundColor White
    Write-Host ""
    exit 1
}
Write-Host "  IBM Cloud CLI installed" -ForegroundColor Green
Write-Host ""

# Check if Code Engine plugin is installed
Write-Host "Checking Code Engine plugin..." -ForegroundColor Cyan
$cePlugin = ibmcloud plugin list 2>$null | Select-String "code-engine"
if (-not $cePlugin) {
    Write-Host "  Code Engine plugin not installed. Installing..." -ForegroundColor Yellow
    ibmcloud plugin install code-engine -f
    Write-Host "  Code Engine plugin installed" -ForegroundColor Green
} else {
    Write-Host "  Code Engine plugin installed" -ForegroundColor Green
}
Write-Host ""

# Check if logged in
Write-Host "Checking IBM Cloud login status..." -ForegroundColor Cyan
$loginStatus = ibmcloud target 2>&1
if ($loginStatus -match "Not logged in") {
    Write-Host "  Not logged in to IBM Cloud" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Logging in with SSO..." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "A browser window will open for SSO authentication." -ForegroundColor Cyan
    Write-Host "Please complete the authentication in your browser." -ForegroundColor Cyan
    Write-Host ""
    
    # Login with SSO
    ibmcloud login --sso
    
    Write-Host ""
}
Write-Host "  Logged in to IBM Cloud" -ForegroundColor Green
Write-Host ""

# Get and select resource group
if (-not $ResourceGroup) {
    Write-Host "Available Resource Groups:" -ForegroundColor Cyan
    $resourceGroups = ibmcloud resource groups --output json | ConvertFrom-Json
    
    if ($resourceGroups.Count -eq 0) {
        Write-Host "  No resource groups found!" -ForegroundColor Red
        exit 1
    }
    
    for ($i = 0; $i -lt $resourceGroups.Count; $i++) {
        Write-Host "  [$($i+1)] $($resourceGroups[$i].name)" -ForegroundColor White
    }
    Write-Host ""
    
    $selection = Read-Host "Select resource group number (1-$($resourceGroups.Count))"
    $ResourceGroup = $resourceGroups[[int]$selection - 1].name
}

Write-Host "Targeting resource group: $ResourceGroup" -ForegroundColor Cyan
ibmcloud target -g $ResourceGroup
Write-Host ""

# Target region
Write-Host "Targeting region: $Region" -ForegroundColor Cyan
ibmcloud target -r $Region
Write-Host ""

# Check if project exists
Write-Host "Checking for Code Engine project: $ProjectName" -ForegroundColor Cyan
$projectExists = ibmcloud ce project list 2>$null | Select-String $ProjectName
if (-not $projectExists) {
    Write-Host "  Project does not exist. Creating..." -ForegroundColor Yellow
    ibmcloud ce project create --name $ProjectName
    Write-Host "  Project created" -ForegroundColor Green
} else {
    Write-Host "  Project exists" -ForegroundColor Green
}
Write-Host ""

# Select project
Write-Host "Selecting project: $ProjectName" -ForegroundColor Cyan
ibmcloud ce project select --name $ProjectName
Write-Host ""

# Check if application exists
Write-Host "Checking if application exists: $AppName" -ForegroundColor Cyan
$appExists = ibmcloud ce application list 2>$null | Select-String $AppName
Write-Host ""

if ($appExists) {
    Write-Host "Application exists. Updating..." -ForegroundColor Yellow
    Write-Host ""
    
    # Update existing application
    ibmcloud ce application update `
        --name $AppName `
        --build-source . `
        --build-context-dir . `
        --strategy dockerfile `
        --wait
} else {
    Write-Host "Creating new application..." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Configuration:" -ForegroundColor Cyan
    Write-Host "  - Port: 8080" -ForegroundColor White
    Write-Host "  - Min scale: 1 (always running)" -ForegroundColor White
    Write-Host "  - Max scale: 3 (auto-scales)" -ForegroundColor White
    Write-Host "  - CPU: 1 vCPU" -ForegroundColor White
    Write-Host "  - Memory: 2GB" -ForegroundColor White
    Write-Host ""
    
    # Create new application
    ibmcloud ce application create `
        --name $AppName `
        --build-source . `
        --build-context-dir . `
        --strategy dockerfile `
        --port 8080 `
        --min-scale 1 `
        --max-scale 3 `
        --cpu 1 `
        --memory 2G `
        --wait
}

Write-Host ""
Write-Host "================================================================================"
Write-Host "Deployment Complete!" -ForegroundColor Green
Write-Host "================================================================================"
Write-Host ""

# Get application URL
Write-Host "Getting application URL..." -ForegroundColor Cyan
$appInfo = ibmcloud ce application get --name $AppName --output json | ConvertFrom-Json
$appUrl = $appInfo.status.url

Write-Host ""
Write-Host "Scraper Service URL:" -ForegroundColor Green
Write-Host "  $appUrl" -ForegroundColor White
Write-Host ""

# Test the service
Write-Host "Testing service..." -ForegroundColor Cyan
try {
    $healthResponse = Invoke-WebRequest -Uri "$appUrl/health" -UseBasicParsing -TimeoutSec 10
    Write-Host "  Health check: OK" -ForegroundColor Green
    Write-Host "  Response: $($healthResponse.Content)" -ForegroundColor White
} catch {
    Write-Host "  Health check failed (service may still be starting)" -ForegroundColor Yellow
    Write-Host "  Wait a minute and try: curl $appUrl/health" -ForegroundColor White
}

Write-Host ""
Write-Host "================================================================================"
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "================================================================================"
Write-Host ""
Write-Host "1. Test the scraper:" -ForegroundColor White
Write-Host "   curl $appUrl/health" -ForegroundColor Yellow
Write-Host "   curl $appUrl/scrape-e1180" -ForegroundColor Yellow
Write-Host ""
Write-Host "2. Update your RAG backend:" -ForegroundColor White
Write-Host "   oc set env deployment/rag-backend SCRAPER_URL=$appUrl" -ForegroundColor Yellow
Write-Host ""
Write-Host "3. Test bulk ingestion from the UI" -ForegroundColor White
Write-Host ""
Write-Host "4. Monitor logs:" -ForegroundColor White
Write-Host "   ibmcloud ce application logs --name $AppName --follow" -ForegroundColor Yellow
Write-Host ""
Write-Host "================================================================================"

# Made with Bob
