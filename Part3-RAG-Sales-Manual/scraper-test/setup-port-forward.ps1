# Setup Port Forwarding for Scraper Service

Write-Host "================================================================================"
Write-Host "Setting up Port Forwarding for Scraper Service"
Write-Host "================================================================================"
Write-Host ""

Write-Host "Prerequisites:" -ForegroundColor Cyan
Write-Host "  1. Scraper service must be running on localhost:5000" -ForegroundColor White
Write-Host "  2. Run start-windows-service.ps1 in another window" -ForegroundColor White
Write-Host ""
Write-Host "Make sure the scraper service is running before continuing!" -ForegroundColor Yellow
Write-Host ""

# Get the backend pod name
Write-Host "Finding backend pod..." -ForegroundColor Cyan
$podName = oc get pods -l app=rag-backend -o jsonpath='{.items[0].metadata.name}' 2>$null

if (-not $podName) {
    Write-Host "  Could not find backend pod!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Make sure you're logged into OpenShift:" -ForegroundColor Yellow
    Write-Host "  oc login ..." -ForegroundColor White
    Write-Host ""
    exit 1
}

Write-Host "  Found pod: $podName" -ForegroundColor Green
Write-Host ""

Write-Host "Setting up reverse port forward..." -ForegroundColor Cyan
Write-Host ""
Write-Host "How it works:" -ForegroundColor White
Write-Host "  1. Your scraper runs on localhost:5000 (this laptop)" -ForegroundColor White
Write-Host "  2. This script forwards requests FROM the backend pod" -ForegroundColor White
Write-Host "  3. TO your laptop's scraper service" -ForegroundColor White
Write-Host "  4. Backend calls localhost:5000 -> reaches your laptop!" -ForegroundColor White
Write-Host ""
Write-Host "IMPORTANT: Keep this window open while using bulk ingestion!" -ForegroundColor Yellow
Write-Host "Press Ctrl+C to stop port forwarding" -ForegroundColor Yellow
Write-Host ""
Write-Host "================================================================================"
Write-Host ""
Write-Host "Port forward active - Backend can now reach your scraper!" -ForegroundColor Green
Write-Host ""

# Start port forwarding
oc port-forward pod/$podName 5000:5000

# Made with Bob
