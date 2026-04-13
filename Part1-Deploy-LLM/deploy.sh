#!/bin/bash

# Deploy LLM Service with Dual Model Support
# This script builds and deploys the llama-service with both TinyLlama and Granite models

set -e

echo "=========================================="
echo "LLM Service Deployment Script"
echo "=========================================="
echo ""

# Check if we're logged into OpenShift
if ! oc whoami &> /dev/null; then
    echo "❌ Error: Not logged into OpenShift"
    echo "Please run: oc login <your-cluster-url>"
    exit 1
fi

# Get current project
PROJECT=$(oc project -q)
echo "📦 Current project: $PROJECT"
echo ""

# Ask which model to use by default
echo "Which model should be used by default?"
echo "1) TinyLlama (recommended for Part 1 - basic demos)"
echo "2) Granite 4.0 Micro (recommended for Part 2/3 - RAG)"
read -p "Enter choice [1-2]: " MODEL_CHOICE

case $MODEL_CHOICE in
    1)
        DEFAULT_MODEL="tinyllama"
        echo "✓ Will use TinyLlama by default"
        ;;
    2)
        DEFAULT_MODEL="granite"
        echo "✓ Will use Granite 4.0 Micro by default"
        ;;
    *)
        echo "⚠️  Invalid choice, defaulting to TinyLlama"
        DEFAULT_MODEL="tinyllama"
        ;;
esac
echo ""

# Check if build config exists
if oc get bc/llama-service &> /dev/null; then
    echo "📦 Build config 'llama-service' already exists"
    read -p "Do you want to rebuild? [y/N]: " REBUILD
    if [[ $REBUILD =~ ^[Yy]$ ]]; then
        echo "🔨 Starting rebuild..."
        oc start-build llama-service --from-dir=. --follow
    else
        echo "⏭️  Skipping rebuild"
    fi
else
    echo "🔨 Creating new build config..."
    oc new-build --name llama-service --binary --strategy docker
    echo "🔨 Starting initial build..."
    oc start-build llama-service --from-dir=. --follow
fi
echo ""

# Update deployment with selected model
echo "📝 Updating deployment configuration..."
sed "s/value: \"tinyllama\"/value: \"$DEFAULT_MODEL\"/" llama-deploy.yaml > llama-deploy-temp.yaml

# Apply Kubernetes resources
echo "🚀 Applying deployment..."
oc apply -f llama-deploy-temp.yaml
rm llama-deploy-temp.yaml

echo "🌐 Applying service..."
oc apply -f llama-svc.yaml

echo "🔗 Applying route..."
oc apply -f llama-route.yaml

echo ""
echo "⏳ Waiting for deployment to be ready..."
oc rollout status deployment/llama-service --timeout=5m

echo ""
echo "=========================================="
echo "✅ Deployment Complete!"
echo "=========================================="
echo ""

# Get the route URL
ROUTE_URL=$(oc get route llama-service -o jsonpath='{.spec.host}' 2>/dev/null || echo "")

if [ -n "$ROUTE_URL" ]; then
    echo "🌐 LLM Service URL: https://$ROUTE_URL"
    echo ""
    echo "You can access the llama.cpp web interface at the URL above."
else
    echo "⚠️  Could not retrieve route URL. Check with: oc get route llama-service"
fi

echo ""
echo "📊 Current model: $DEFAULT_MODEL"
echo ""
echo "To switch models later, run:"
echo "  oc set env deployment/llama-service LLM_MODEL=tinyllama"
echo "  oc set env deployment/llama-service LLM_MODEL=granite"
echo ""
echo "To check logs:"
echo "  oc logs -f deployment/llama-service"
echo ""
echo "To verify which model is running:"
echo "  oc logs deployment/llama-service | grep 'Starting with'"
echo ""

# Made with Bob
