# Redeploy RAG Backend with new endpoint
# Rebuilds container and restarts deployment

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "  Redeploying RAG Backend with /ingest-scraped-content endpoint" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""

$PROJECT = "llm-on-techzone"

Write-Host "[1/4] Starting new build..." -ForegroundColor Yellow
oc start-build rag-backend --from-dir=. --follow

if ($LASTEXITCODE -ne 0) {
    Write-Host "  X Build failed!" -ForegroundColor Red
    exit 1
}
Write-Host "  OK Build complete" -ForegroundColor Green

Write-Host ""
Write-Host "[2/4] Restarting deployment..." -ForegroundColor Yellow
oc rollout restart deployment/rag-backend

if ($LASTEXITCODE -ne 0) {
    Write-Host "  X Restart failed!" -ForegroundColor Red
    exit 1
}
Write-Host "  OK Deployment restarted" -ForegroundColor Green

Write-Host ""
Write-Host "[3/4] Waiting for rollout..." -ForegroundColor Yellow
oc rollout status deployment/rag-backend --timeout=5m

if ($LASTEXITCODE -ne 0) {
    Write-Host "  X Rollout failed!" -ForegroundColor Red
    exit 1
}
Write-Host "  OK Rollout complete" -ForegroundColor Green

Write-Host ""
Write-Host "[4/4] Checking pod status..." -ForegroundColor Yellow
$pods = oc get pods -l app=rag-backend --field-selector=status.phase=Running -o name
if ($pods) {
    Write-Host "  OK Backend pod running" -ForegroundColor Green
    Write-Host "  Pods: $pods" -ForegroundColor Gray
} else {
    Write-Host "  X No running pods found" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "================================================================================" -ForegroundColor Green
Write-Host "  Deployment Complete!" -ForegroundColor Green
Write-Host "================================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Backend URL: https://rag-backend-llm-on-techzone.apps.p1219.cecc.ihost.com" -ForegroundColor Cyan
Write-Host ""
Write-Host "Test the new endpoint:" -ForegroundColor Cyan
Write-Host '  cd ..\scraper-test' -ForegroundColor Gray
Write-Host '  .\test-backend-integration.ps1' -ForegroundColor Gray
Write-Host ""

# Made with Bob
