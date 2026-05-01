# Deploy RAG Backend with OpenSearch to OpenShift (PowerShell)
# This script deploys the backend service that connects to an existing OpenSearch cluster

$ErrorActionPreference = "Stop"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "RAG Backend with OpenSearch Deployment" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# Check if logged into OpenShift
try {
    $null = oc whoami 2>&1
} catch {
    Write-Host "Error: Not logged into OpenShift. Please run 'oc login' first." -ForegroundColor Red
    exit 1
}

$PROJECT = oc project -q
Write-Host "Deploying to project: $PROJECT" -ForegroundColor Green

# Configuration
$APP_NAME = "rag-backend-opensearch"
$IMAGE_NAME = "${APP_NAME}:latest"

Write-Host ""
Write-Host "Step 1: Creating BuildConfig..." -ForegroundColor Yellow
@"
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
      dockerfilePath: Dockerfile.opensearch
  triggers: []
"@ | oc apply -f -

Write-Host ""
Write-Host "Step 2: Creating ImageStream..." -ForegroundColor Yellow
oc create imagestream $APP_NAME --dry-run=client -o yaml | oc apply -f -

Write-Host ""
Write-Host "Step 3: Starting build from local directory..." -ForegroundColor Yellow
oc start-build $APP_NAME --from-dir=. --follow

Write-Host ""
Write-Host "Step 4: Creating Deployment..." -ForegroundColor Yellow
@"
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
"@ | oc apply -f -

Write-Host ""
Write-Host "Step 5: Creating Service..." -ForegroundColor Yellow
@"
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
"@ | oc apply -f -

Write-Host ""
Write-Host "Step 6: Creating Route..." -ForegroundColor Yellow
@"
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
"@ | oc apply -f -

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Deployment Complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Getting route URL..." -ForegroundColor Yellow
$ROUTE_URL = oc get route $APP_NAME -o jsonpath='{.spec.host}'
Write-Host ""
Write-Host "RAG Backend URL: https://$ROUTE_URL" -ForegroundColor Green
Write-Host ""
Write-Host "Test the service:" -ForegroundColor Yellow
Write-Host "  curl https://$ROUTE_URL/health" -ForegroundColor White
Write-Host ""
Write-Host "Note: Make sure OpenSearch is deployed and accessible at opensearch-service:9200" -ForegroundColor Yellow
Write-Host ""

# Made with Bob
