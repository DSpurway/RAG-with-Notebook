# Deploy RAG Backend with ChromaDB (PowerShell version)
# Run from RAG-with-Notebook directory

$ErrorActionPreference = "Stop"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "RAG Backend ChromaDB Deployment" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Check if we're in the right directory
if (-not (Test-Path "rag-backend")) {
    Write-Host "❌ Error: Must run from RAG-with-Notebook directory" -ForegroundColor Red
    Write-Host "Current directory: $(Get-Location)" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Directory check passed" -ForegroundColor Green
Write-Host ""

# Step 1: Create PVC
Write-Host "Step 1: Creating Persistent Volume Claim..." -ForegroundColor Yellow
oc apply -f rag-backend/rag-backend-pvc.yaml
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to create PVC" -ForegroundColor Red
    exit 1
}
Write-Host "✅ PVC created" -ForegroundColor Green
Write-Host ""

# Step 2: Build image
Write-Host "Step 2: Building RAG Backend image..." -ForegroundColor Yellow
Push-Location rag-backend

# Check if build config exists
$bcExists = oc get bc/rag-backend 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Creating new build config..." -ForegroundColor Yellow
    oc new-build --name rag-backend --binary --strategy docker
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to create build config" -ForegroundColor Red
        exit 1
    }
}

Write-Host "Starting build..." -ForegroundColor Yellow
Write-Host "NOTE: Check build output for 'Failed building wheel' errors" -ForegroundColor Yellow
Write-Host ""

# Run build - let output stream naturally
oc start-build rag-backend --from-dir=. --follow

if ($LASTEXITCODE -ne 0) {
    Write-Host "" -ForegroundColor Red
    Write-Host "❌ Build command failed with exit code $LASTEXITCODE" -ForegroundColor Red
    Write-Host "" -ForegroundColor Red
    Write-Host "Common issues:" -ForegroundColor Yellow
    Write-Host "  - Check build logs above for 'Failed building wheel' errors" -ForegroundColor Yellow
    Write-Host "  - Missing dependencies from IBM wheels" -ForegroundColor Yellow
    Write-Host "  - Packages being reinstalled from requirements.txt" -ForegroundColor Yellow
    Write-Host "" -ForegroundColor Yellow
    Write-Host "If you see 'Failed building wheel' errors, the build failed even if exit code is 0" -ForegroundColor Yellow
    Write-Host ""
    exit 1
}

Write-Host "" -ForegroundColor Green
Write-Host "✅ Build command completed" -ForegroundColor Green
Write-Host "⚠️  IMPORTANT: Check output above for 'Failed building wheel' errors" -ForegroundColor Yellow
Write-Host "    If you see any, the build actually failed and you should not proceed" -ForegroundColor Yellow
Write-Host ""

# Give user a chance to abort if they saw errors
Write-Host "Press Ctrl+C within 5 seconds to abort if you saw build errors..." -ForegroundColor Yellow
Start-Sleep -Seconds 5
Write-Host ""

# Step 3: Deploy
Write-Host "Step 3: Deploying RAG Backend..." -ForegroundColor Yellow
oc apply -f rag-backend-deploy.yaml
oc apply -f rag-backend-svc.yaml
oc apply -f rag-backend-route.yaml
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Deployment failed" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Deployment created" -ForegroundColor Green
Write-Host ""

# Step 4: Wait for deployment
Write-Host "Step 4: Waiting for deployment to be ready..." -ForegroundColor Yellow
oc rollout status deployment/rag-backend --timeout=5m

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Deployment failed to become ready" -ForegroundColor Red
    Write-Host "Check logs with: oc logs -f deployment/rag-backend" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Deployment ready" -ForegroundColor Green
Write-Host ""

# Step 5: Get route
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Deployment Complete!" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

$route = oc get route rag-backend -o jsonpath='{.spec.host}'
Write-Host "RAG Backend URL: https://$route" -ForegroundColor Green
Write-Host ""
Write-Host "Test endpoints:" -ForegroundColor Yellow
Write-Host "  Health:      curl https://$route/health"
Write-Host "  Collections: curl https://$route/api/collections"
Write-Host ""
Write-Host "View logs:" -ForegroundColor Yellow
Write-Host "  oc logs -f deployment/rag-backend"
Write-Host ""

# Return to parent directory
Pop-Location

# Made with Bob
