#!/bin/bash
# Deploy RAG Backend to OpenShift
# This script deploys the backend service with OpenSearch support

set -e

echo "=========================================="
echo "RAG Backend Deployment"
echo "=========================================="

# Check if logged into OpenShift
if ! oc whoami &> /dev/null; then
    echo "Error: Not logged into OpenShift. Please run 'oc login' first."
    exit 1
fi

PROJECT=$(oc project -q)
echo "Deploying to project: $PROJECT"

# Configuration
APP_NAME="rag-backend-opensearch"
IMAGE_NAME="$APP_NAME:latest"

echo ""
echo "Step 1: Creating BuildConfig..."
cat <<EOF | oc apply -f -
apiVersion: build.openshift.io/v1
kind: BuildConfig
metadata:
  name: $APP_NAME
spec:
  output:
    to:
      kind: ImageStreamTag
      name: $IMAGE_NAME
  source:
    type: Binary
    binary: {}
  strategy:
    type: Docker
    dockerStrategy:
      dockerfilePath: Dockerfile
  triggers: []
EOF

echo ""
echo "Step 2: Creating ImageStream..."
oc create imagestream $APP_NAME --dry-run=client -o yaml | oc apply -f -

echo ""
echo "Step 3: Starting build from local directory..."
oc start-build $APP_NAME --from-dir=. --follow

echo ""
echo "Step 4: Creating Deployment..."
cat <<EOF | oc apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: $APP_NAME
  labels:
    app: $APP_NAME
spec:
  replicas: 1
  selector:
    matchLabels:
      app: $APP_NAME
  template:
    metadata:
      labels:
        app: $APP_NAME
    spec:
      containers:
      - name: rag-backend
        image: image-registry.openshift-image-registry.svc:5000/$PROJECT/$IMAGE_NAME
        ports:
        - containerPort: 8080
          protocol: TCP
        env:
        - name: OPENSEARCH_HOST
          value: "opensearch-service"
        - name: OPENSEARCH_PORT
          value: "9200"
        - name: OPENSEARCH_USERNAME
          value: "admin"
        - name: OPENSEARCH_PASSWORD
          value: "admin"
        - name: OPENSEARCH_DB_PREFIX
          value: "rag"
        - name: OPENSEARCH_INDEX_NAME
          value: "default"
        - name: OPENSEARCH_NUM_SHARDS
          value: "1"
        - name: LLAMA_HOST
          value: "llama-service"
        - name: LLAMA_PORT
          value: "8080"
        - name: PDF_DIR
          value: "/app/pdfs"
        - name: CORS_ORIGIN
          value: "*"
        resources:
          requests:
            memory: "2Gi"
            cpu: "500m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 60
          periodSeconds: 30
          timeoutSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
EOF

echo ""
echo "Step 5: Creating Service..."
cat <<EOF | oc apply -f -
apiVersion: v1
kind: Service
metadata:
  name: $APP_NAME
  labels:
    app: $APP_NAME
spec:
  ports:
  - port: 8080
    targetPort: 8080
    protocol: TCP
    name: http
  selector:
    app: $APP_NAME
  type: ClusterIP
EOF

echo ""
echo "Step 6: Creating Route..."
cat <<EOF | oc apply -f -
apiVersion: route.openshift.io/v1
kind: Route
metadata:
  name: $APP_NAME
  labels:
    app: $APP_NAME
spec:
  to:
    kind: Service
    name: $APP_NAME
  port:
    targetPort: http
  tls:
    termination: edge
    insecureEdgeTerminationPolicy: Redirect
EOF

echo ""
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo ""
echo "Getting route URL..."
ROUTE_URL=$(oc get route $APP_NAME -o jsonpath='{.spec.host}')
echo ""
echo "RAG Backend URL: https://$ROUTE_URL"
echo ""
echo "Test the service:"
echo "  curl https://$ROUTE_URL/health"
echo ""
echo "Note: Make sure OpenSearch is deployed and accessible at opensearch-service:9200"
echo ""

# Made with Bob
