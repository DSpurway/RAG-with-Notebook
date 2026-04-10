#!/bin/bash

# Setup script for Part 3 - RAG with Sales Manuals
# This script helps configure environment variables for all services

set -e

echo "=========================================="
echo "Part 3 RAG Sales Manual Setup"
echo "=========================================="
echo ""

# Get the current project
CURRENT_PROJECT=$(oc project -q 2>/dev/null || echo "")

if [ -z "$CURRENT_PROJECT" ]; then
    echo "Error: Not logged into OpenShift. Please run 'oc login' first."
    exit 1
fi

echo "Current OpenShift project: $CURRENT_PROJECT"
echo ""

# Prompt for TechZone environment number if not set
if [ -z "$TECHZONE_ENV" ]; then
    read -p "Enter your TechZone environment number (e.g., p1293): " TECHZONE_ENV
fi

# Construct base domain
BASE_DOMAIN="apps.${TECHZONE_ENV}.cecc.ihost.com"
echo "Using base domain: $BASE_DOMAIN"
echo ""

# Construct webpage URL for CORS
WEBPAGE_URL="https://rag-webpage-${CURRENT_PROJECT}.${BASE_DOMAIN}"
echo "Webpage URL will be: $WEBPAGE_URL"
echo ""

# Ask if user wants to set CORS origin
read -p "Do you want to set CORS origin to the webpage URL? (y/n, default: n for wildcard): " SET_CORS
SET_CORS=${SET_CORS:-n}

if [[ "$SET_CORS" =~ ^[Yy]$ ]]; then
    CORS_ORIGIN="$WEBPAGE_URL"
    echo "CORS origin will be set to: $CORS_ORIGIN"
else
    CORS_ORIGIN="*"
    echo "CORS origin will be set to: * (wildcard - allows all origins)"
fi
echo ""

# List of services to configure
SERVICES=(
    "rag-list-collections"
    "rag-drop-collection"
    "rag-loader"
    "rag-get-docs"
    "rag-prompt-llm"
)

echo "Configuring CORS for services..."
for service in "${SERVICES[@]}"; do
    if oc get deployment "$service" &>/dev/null; then
        echo "  Setting CORS_ORIGIN for $service..."
        oc set env deployment/"$service" CORS_ORIGIN="$CORS_ORIGIN"
    else
        echo "  Warning: Deployment $service not found. Skipping."
    fi
done
echo ""

# Configure RAG-Webpage with service URLs
echo "Configuring RAG-Webpage with service URLs..."
if oc get deployment rag-webpage &>/dev/null; then
    oc set env deployment/rag-webpage \
        NAMESPACE="$CURRENT_PROJECT" \
        BASE_DOMAIN="$BASE_DOMAIN" \
        RAG_LIST_COLLECTIONS_URL="https://rag-list-collections-${CURRENT_PROJECT}.${BASE_DOMAIN}" \
        RAG_DROP_COLLECTION_URL="https://rag-drop-collection-${CURRENT_PROJECT}.${BASE_DOMAIN}" \
        RAG_LOADER_URL="https://rag-loader-${CURRENT_PROJECT}.${BASE_DOMAIN}" \
        RAG_GET_DOCS_URL="https://rag-get-docs-${CURRENT_PROJECT}.${BASE_DOMAIN}" \
        RAG_PROMPT_LLM_URL="https://rag-prompt-llm-${CURRENT_PROJECT}.${BASE_DOMAIN}"
    echo "  RAG-Webpage configured successfully"
else
    echo "  Warning: Deployment rag-webpage not found. Skipping."
fi
echo ""

echo "=========================================="
echo "Configuration Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Wait for all pods to restart (this may take a minute)"
echo "2. Access the webpage at: $WEBPAGE_URL"
echo "3. Test the 'List Collections' button to verify CORS is working"
echo ""
echo "To check pod status:"
echo "  oc get pods -l app=sales-manual-rag-app"
echo ""
echo "To view logs for a specific service:"
echo "  oc logs -f deployment/rag-list-collections"
echo ""

# Made with Bob
