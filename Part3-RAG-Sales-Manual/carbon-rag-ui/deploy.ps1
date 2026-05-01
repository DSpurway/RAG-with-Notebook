# Carbon RAG UI Deployment Script for OpenShift (PowerShell)
# This script builds and deploys the carbon-rag-ui to OpenShift

$ErrorActionPreference = "Stop"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Carbon RAG UI - OpenShift Deployment" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Get current project
$PROJECT = oc project -q
Write-Host "Current OpenShift project: $PROJECT" -ForegroundColor Green
Write-Host ""

# Check if rag-backend is running
Write-Host "Checking rag-backend status..."
try {
    $null = oc get deployment rag-backend 2>&1
} catch {
    Write-Host "ERROR: rag-backend deployment not found!" -ForegroundColor Red
    Write-Host "Please deploy the rag-backend first." -ForegroundColor Red
    exit 1
}

$RAG_BACKEND_ROUTE = oc get route rag-backend -o jsonpath="{.spec.host}" 2>$null
if ([string]::IsNullOrEmpty($RAG_BACKEND_ROUTE)) {
    Write-Host "ERROR: rag-backend route not found!" -ForegroundColor Red
    exit 1
}

Write-Host "✓ rag-backend found at: https://$RAG_BACKEND_ROUTE" -ForegroundColor Green
Write-Host ""

# Build the Docker image
Write-Host "Building Docker image..." -ForegroundColor Yellow
Write-Host "This may take a few minutes..."
podman build -t carbon-rag-ui:latest .

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Docker build failed!" -ForegroundColor Red
    exit 1
}

Write-Host "✓ Docker image built successfully" -ForegroundColor Green
Write-Host ""

# Tag for OpenShift internal registry
$REGISTRY = oc get route default-route -n openshift-image-registry -o jsonpath="{.spec.host}" 2>$null

if (-not [string]::IsNullOrEmpty($REGISTRY)) {
    Write-Host "Tagging image for OpenShift registry..."
    podman tag carbon-rag-ui:latest "$REGISTRY/$PROJECT/carbon-rag-ui:latest"
    
    Write-Host "Logging into OpenShift registry..."
    $TOKEN = oc whoami -t
    $USER = oc whoami
    podman login -u $USER -p $TOKEN $REGISTRY --tls-verify=false
    
    Write-Host "Pushing image to OpenShift registry..."
    podman push "$REGISTRY/$PROJECT/carbon-rag-ui:latest" --tls-verify=false
    
    Write-Host "✓ Image pushed to OpenShift registry" -ForegroundColor Green
    Write-Host ""
    
    # Update deployment YAML to use registry image
    $deploymentContent = Get-Content openshift-deployment.yaml -Raw
    $deploymentContent = $deploymentContent -replace "image: carbon-rag-ui:latest", "image: image-registry.openshift-image-registry.svc:5000/$PROJECT/carbon-rag-ui:latest"
    $deploymentContent | Set-Content openshift-deployment-temp.yaml
} else {
    Write-Host "WARNING: OpenShift internal registry not accessible" -ForegroundColor Yellow
    Write-Host "Using local image. Make sure nodes can access it."
    Write-Host ""
    Copy-Item openshift-deployment.yaml openshift-deployment-temp.yaml
}

# Update backend URL in deployment
Write-Host "Updating backend URL in deployment..."
$deploymentContent = Get-Content openshift-deployment-temp.yaml -Raw
$deploymentContent = $deploymentContent -replace 'value: "https://rag-backend[^"]*"', "value: ""https://$RAG_BACKEND_ROUTE"""
$deploymentContent | Set-Content openshift-deployment-temp.yaml

# Deploy to OpenShift
Write-Host "Deploying to OpenShift..."
oc apply -f openshift-deployment-temp.yaml

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Deployment failed!" -ForegroundColor Red
    Remove-Item openshift-deployment-temp.yaml -ErrorAction SilentlyContinue
    exit 1
}

Write-Host "✓ Deployment created" -ForegroundColor Green
Write-Host ""

# Wait for deployment to be ready
Write-Host "Waiting for deployment to be ready..."
oc rollout status deployment/carbon-rag-ui --timeout=5m

if ($LASTEXITCODE -ne 0) {
    Write-Host "WARNING: Deployment rollout timed out or failed" -ForegroundColor Yellow
    Write-Host "Check pod status with: oc get pods -l app=carbon-rag-ui"
    Write-Host "Check logs with: oc logs -f deployment/carbon-rag-ui"
} else {
    Write-Host "✓ Deployment ready" -ForegroundColor Green
}

Write-Host ""

# Get the route
$UI_ROUTE = oc get route carbon-rag-ui -o jsonpath="{.spec.host}" 2>$null

if (-not [string]::IsNullOrEmpty($UI_ROUTE)) {
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host "Deployment Complete!" -ForegroundColor Cyan
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Carbon RAG UI URL: https://$UI_ROUTE" -ForegroundColor Green
    Write-Host "Backend URL: https://$RAG_BACKEND_ROUTE" -ForegroundColor Green
    Write-Host ""
    Write-Host "Test the deployment:" -ForegroundColor Yellow
    Write-Host "  1. Open https://$UI_ROUTE in your browser"
    Write-Host "  2. Navigate to the RAG Demo tab"
    Write-Host "  3. Try Part 2 (Harry Potter) or Part 3 (Sales Manual)"
    Write-Host ""
    Write-Host "Monitor the deployment:" -ForegroundColor Yellow
    Write-Host "  oc get pods -l app=carbon-rag-ui"
    Write-Host "  oc logs -f deployment/carbon-rag-ui"
    Write-Host ""
} else {
    Write-Host "WARNING: Could not get route URL" -ForegroundColor Yellow
    Write-Host "Check route with: oc get route carbon-rag-ui"
}

# Cleanup temp file
Remove-Item openshift-deployment-temp.yaml -ErrorAction SilentlyContinue

Write-Host "Done!" -ForegroundColor Green

# Made with Bob
