#!/bin/bash

# IBM Docs Selenium Scraper - Deployment Script
# Deploys the scraper service to OpenShift

set -e

echo "=========================================="
echo "IBM Docs Selenium Scraper Deployment"
echo "=========================================="
echo ""

# Check if oc is available
if ! command -v oc &> /dev/null; then
    echo "❌ Error: 'oc' command not found"
    echo "Please install OpenShift CLI and login first"
    exit 1
fi

# Check if logged in
if ! oc whoami &> /dev/null; then
    echo "❌ Error: Not logged into OpenShift"
    echo "Please run: oc login <cluster-url>"
    exit 1
fi

echo "✅ Logged in as: $(oc whoami)"
echo "✅ Current project: $(oc project -q)"
echo ""

# Check if build config exists
if oc get bc/selenium-scraper &> /dev/null; then
    echo "📦 Build config 'selenium-scraper' already exists"
    echo "   Updating existing build..."
else
    echo "📦 Creating new build config..."
    oc new-build --name selenium-scraper --binary --strategy docker
fi

echo ""
echo "🔨 Building container image..."
oc start-build selenium-scraper --from-dir=. --follow

if [ $? -ne 0 ]; then
    echo "❌ Build failed!"
    exit 1
fi

echo ""
echo "✅ Build completed successfully"
echo ""

# Check if deployment exists
if oc get deployment/selenium-scraper &> /dev/null; then
    echo "🚀 Deployment 'selenium-scraper' already exists"
    echo "   Triggering rollout..."
    oc rollout restart deployment/selenium-scraper
    oc rollout status deployment/selenium-scraper
else
    echo "🚀 Creating new deployment..."
    oc new-app selenium-scraper
    
    # Wait for deployment
    echo "   Waiting for deployment to complete..."
    oc rollout status deployment/selenium-scraper
fi

echo ""

# Check if route exists
if oc get route/selenium-scraper &> /dev/null; then
    echo "🌐 Route already exists"
else
    echo "🌐 Creating route..."
    oc expose svc/selenium-scraper
fi

echo ""
echo "=========================================="
echo "✅ Deployment Complete!"
echo "=========================================="
echo ""

# Get route URL
ROUTE=$(oc get route selenium-scraper -o jsonpath='{.spec.host}')
echo "🔗 Service URL: http://$ROUTE"
echo ""

echo "📋 Available endpoints:"
echo "   Health check:  http://$ROUTE/health"
echo "   Test E1180:    http://$ROUTE/scrape-e1180"
echo "   Scrape custom: http://$ROUTE/scrape?url=<ibm-docs-url>"
echo "   Full extract:  http://$ROUTE/extract-content?url=<ibm-docs-url>"
echo ""

echo "🧪 Test the service:"
echo "   curl http://$ROUTE/health"
echo "   curl http://$ROUTE/scrape-e1180"
echo ""

echo "📊 View logs:"
echo "   oc logs -f deployment/selenium-scraper"
echo ""

echo "🔍 Check status:"
echo "   oc get pods -l app=selenium-scraper"
echo ""

# Made with Bob
