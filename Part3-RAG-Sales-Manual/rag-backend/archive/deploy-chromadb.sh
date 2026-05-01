#!/bin/bash
# Deploy RAG Backend with ChromaDB
# Run from RAG-with-Notebook directory

set -e

echo "=========================================="
echo "RAG Backend ChromaDB Deployment"
echo "=========================================="
echo ""

# Check if we're in the right directory
if [ ! -d "rag-backend" ]; then
    echo "❌ Error: Must run from RAG-with-Notebook directory"
    echo "Current directory: $(pwd)"
    exit 1
fi

echo "✅ Directory check passed"
echo ""

# Step 1: Create PVC
echo "Step 1: Creating Persistent Volume Claim..."
oc apply -f rag-backend/rag-backend-pvc.yaml
echo "✅ PVC created"
echo ""

# Step 2: Build image
echo "Step 2: Building RAG Backend image..."
cd rag-backend

# Check if build config exists
if ! oc get bc/rag-backend &>/dev/null; then
    echo "Creating new build config..."
    oc new-build --name rag-backend --binary --strategy docker
fi

echo "Starting build..."
BUILD_OUTPUT=$(oc start-build rag-backend --from-dir=. --follow 2>&1)
BUILD_EXIT=$?

echo "$BUILD_OUTPUT"

# Check for build errors
if [ $BUILD_EXIT -ne 0 ] || echo "$BUILD_OUTPUT" | grep -qE "error:|ERROR:|Failed building wheel"; then
    echo ""
    echo "❌ Build failed - Check output above for errors"
    echo ""
    echo "Common issues:"
    echo "  - Missing dependencies from IBM wheels"
    echo "  - Check that all ChromaDB deps are in first pip install"
    echo ""
    exit 1
fi

echo ""
echo "✅ Build completed successfully"
echo ""

# Step 3: Deploy
echo "Step 3: Deploying RAG Backend..."
oc apply -f rag-backend-deploy.yaml
oc apply -f rag-backend-svc.yaml
oc apply -f rag-backend-route.yaml
echo "✅ Deployment created"
echo ""

# Step 4: Wait for deployment
echo "Step 4: Waiting for deployment to be ready..."
oc rollout status deployment/rag-backend --timeout=5m

if [ $? -ne 0 ]; then
    echo "❌ Deployment failed to become ready"
    echo "Check logs with: oc logs -f deployment/rag-backend"
    exit 1
fi

echo "✅ Deployment ready"
echo ""

# Step 5: Get route
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo ""
ROUTE=$(oc get route rag-backend -o jsonpath='{.spec.host}')
echo "RAG Backend URL: https://$ROUTE"
echo ""
echo "Test endpoints:"
echo "  Health:      curl https://$ROUTE/health"
echo "  Collections: curl https://$ROUTE/api/collections"
echo ""
echo "View logs:"
echo "  oc logs -f deployment/rag-backend"
echo ""

# Made with Bob