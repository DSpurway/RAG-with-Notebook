#!/bin/bash

# Carbon RAG UI Deployment Script for OpenShift
# This script builds and deploys the carbon-rag-ui to OpenShift

set -e

echo "=========================================="
echo "Carbon RAG UI - OpenShift Deployment"
echo "=========================================="
echo ""

# Get current project
PROJECT=$(oc project -q)
echo "Current OpenShift project: $PROJECT"
echo ""

# Check if rag-backend is running
echo "Checking rag-backend status..."
if ! oc get deployment rag-backend &> /dev/null; then
    echo "ERROR: rag-backend deployment not found!"
    echo "Please deploy the rag-backend first."
    exit 1
fi

RAG_BACKEND_ROUTE=$(oc get route rag-backend -o jsonpath='{.spec.host}' 2>/dev/null || echo "")
if [ -z "$RAG_BACKEND_ROUTE" ]; then
    echo "ERROR: rag-backend route not found!"
    exit 1
fi

echo "✓ rag-backend found at: https://$RAG_BACKEND_ROUTE"
echo ""

# Build the Docker image
echo "Building Docker image..."
echo "This may take a few minutes..."
podman build -t carbon-rag-ui:latest .

if [ $? -ne 0 ]; then
    echo "ERROR: Docker build failed!"
    exit 1
fi

echo "✓ Docker image built successfully"
echo ""

# Tag for OpenShift internal registry
REGISTRY=$(oc get route default-route -n openshift-image-registry -o jsonpath='{.spec.host}' 2>/dev/null || echo "")

if [ -n "$REGISTRY" ]; then
    echo "Tagging image for OpenShift registry..."
    podman tag carbon-rag-ui:latest $REGISTRY/$PROJECT/carbon-rag-ui:latest
    
    echo "Logging into OpenShift registry..."
    podman login -u $(oc whoami) -p $(oc whoami -t) $REGISTRY --tls-verify=false
    
    echo "Pushing image to OpenShift registry..."
    podman push $REGISTRY/$PROJECT/carbon-rag-ui:latest --tls-verify=false
    
    echo "✓ Image pushed to OpenShift registry"
    echo ""
    
    # Update deployment YAML to use registry image
    sed -i.bak "s|image: carbon-rag-ui:latest|image: image-registry.openshift-image-registry.svc:5000/$PROJECT/carbon-rag-ui:latest|g" openshift-deployment.yaml
else
    echo "WARNING: OpenShift internal registry not accessible"
    echo "Using local image. Make sure nodes can access it."
    echo ""
fi

# Update backend URL in deployment
echo "Updating backend URL in deployment..."
sed -i.bak "s|value: \"https://rag-backend.*\"|value: \"https://$RAG_BACKEND_ROUTE\"|g" openshift-deployment.yaml

# Deploy to OpenShift
echo "Deploying to OpenShift..."
oc apply -f openshift-deployment.yaml

if [ $? -ne 0 ]; then
    echo "ERROR: Deployment failed!"
    # Restore backup
    mv openshift-deployment.yaml.bak openshift-deployment.yaml
    exit 1
fi

echo "✓ Deployment created"
echo ""

# Wait for deployment to be ready
echo "Waiting for deployment to be ready..."
oc rollout status deployment/carbon-rag-ui --timeout=5m

if [ $? -ne 0 ]; then
    echo "WARNING: Deployment rollout timed out or failed"
    echo "Check pod status with: oc get pods -l app=carbon-rag-ui"
    echo "Check logs with: oc logs -f deployment/carbon-rag-ui"
else
    echo "✓ Deployment ready"
fi

echo ""

# Get the route
UI_ROUTE=$(oc get route carbon-rag-ui -o jsonpath='{.spec.host}' 2>/dev/null || echo "")

if [ -n "$UI_ROUTE" ]; then
    echo "=========================================="
    echo "Deployment Complete!"
    echo "=========================================="
    echo ""
    echo "Carbon RAG UI URL: https://$UI_ROUTE"
    echo "Backend URL: https://$RAG_BACKEND_ROUTE"
    echo ""
    echo "Test the deployment:"
    echo "  1. Open https://$UI_ROUTE in your browser"
    echo "  2. Navigate to the RAG Demo tab"
    echo "  3. Try Part 2 (Harry Potter) or Part 3 (Sales Manual)"
    echo ""
    echo "Monitor the deployment:"
    echo "  oc get pods -l app=carbon-rag-ui"
    echo "  oc logs -f deployment/carbon-rag-ui"
    echo ""
else
    echo "WARNING: Could not get route URL"
    echo "Check route with: oc get route carbon-rag-ui"
fi

# Restore original deployment file
if [ -f openshift-deployment.yaml.bak ]; then
    mv openshift-deployment.yaml.bak openshift-deployment.yaml
fi

echo "Done!"

# Made with Bob
