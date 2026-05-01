# Deploy Scraper Service to IBM Cloud Code Engine

## Prerequisites

1. **IBM Cloud Account** with access to Code Engine
2. **IBM Cloud CLI** installed
3. **Docker** (optional, for local testing)

## Step 1: Install IBM Cloud CLI and Code Engine Plugin

```powershell
# Install IBM Cloud CLI (if not already installed)
# Download from: https://cloud.ibm.com/docs/cli?topic=cli-install-ibmcloud-cli

# Install Code Engine plugin
ibmcloud plugin install code-engine
```

## Step 2: Login to IBM Cloud

```powershell
# Login to IBM Cloud
ibmcloud login

# Target your resource group
ibmcloud target -g <your-resource-group>

# Target a region (e.g., us-south, eu-gb, eu-de)
ibmcloud target -r us-south
```

## Step 3: Create Code Engine Project

```powershell
# Create a new Code Engine project
ibmcloud ce project create --name scraper-service

# Select the project
ibmcloud ce project select --name scraper-service
```

## Step 4: Build and Deploy

### Option A: Build from Source (Recommended)

```powershell
# Navigate to scraper directory
cd C:\Users\029878866\EMEA-AI-SQUAD\RAG-with-Notebook\Part3-RAG-Sales-Manual\scraper-test

# Build and deploy in one command
ibmcloud ce application create `
  --name ibm-docs-scraper `
  --build-source . `
  --build-context-dir . `
  --strategy dockerfile `
  --port 8080 `
  --min-scale 1 `
  --max-scale 3 `
  --cpu 1 `
  --memory 2G `
  --wait
```

### Option B: Build Locally and Push

```powershell
# Build Docker image locally
docker build -t ibm-docs-scraper:latest .

# Tag for IBM Cloud Container Registry
docker tag ibm-docs-scraper:latest us.icr.io/<your-namespace>/ibm-docs-scraper:latest

# Push to registry
docker push us.icr.io/<your-namespace>/ibm-docs-scraper:latest

# Deploy from registry
ibmcloud ce application create `
  --name ibm-docs-scraper `
  --image us.icr.io/<your-namespace>/ibm-docs-scraper:latest `
  --port 8080 `
  --min-scale 1 `
  --max-scale 3 `
  --cpu 1 `
  --memory 2G
```

## Step 5: Get the Service URL

```powershell
# Get application details
ibmcloud ce application get --name ibm-docs-scraper

# The URL will be shown in the output, something like:
# https://ibm-docs-scraper.xxxxxx.us-south.codeengine.appdomain.cloud
```

## Step 6: Test the Service

```powershell
# Get the URL
$SCRAPER_URL = ibmcloud ce application get --name ibm-docs-scraper --output json | ConvertFrom-Json | Select-Object -ExpandProperty status | Select-Object -ExpandProperty url

# Test health endpoint
curl "$SCRAPER_URL/health"

# Test scraping E1180
curl "$SCRAPER_URL/scrape-e1180"
```

## Step 7: Update RAG Backend Configuration

Once deployed, update your RAG backend to use the Code Engine URL:

```powershell
# In your OCP cluster
oc set env deployment/rag-backend SCRAPER_URL=$SCRAPER_URL
```

## Configuration Options

### Scaling
- **min-scale**: Minimum number of instances (1 = always running)
- **max-scale**: Maximum number of instances (auto-scales based on load)
- **cpu**: CPU allocation (0.125, 0.25, 0.5, 1, 2, 4, 6, 8)
- **memory**: Memory allocation (256M, 512M, 1G, 2G, 4G, 8G, 16G, 32G)

### Cost Optimization
```powershell
# For cost savings, use min-scale 0 (scales to zero when idle)
ibmcloud ce application update `
  --name ibm-docs-scraper `
  --min-scale 0 `
  --max-scale 3
```

## Monitoring

```powershell
# View logs
ibmcloud ce application logs --name ibm-docs-scraper

# Follow logs in real-time
ibmcloud ce application logs --name ibm-docs-scraper --follow

# Get application status
ibmcloud ce application get --name ibm-docs-scraper
```

## Updating the Service

```powershell
# After making code changes, rebuild and update
ibmcloud ce application update `
  --name ibm-docs-scraper `
  --build-source . `
  --wait
```

## Troubleshooting

### Check Build Logs
```powershell
ibmcloud ce buildrun list
ibmcloud ce buildrun logs --name <buildrun-name>
```

### Check Application Logs
```powershell
ibmcloud ce application logs --name ibm-docs-scraper --tail 100
```

### Test Locally First
```powershell
# Build and run locally
docker build -t ibm-docs-scraper:latest .
docker run -p 8080:8080 ibm-docs-scraper:latest

# Test
curl http://localhost:8080/health
```

## Cleanup

```powershell
# Delete application
ibmcloud ce application delete --name ibm-docs-scraper

# Delete project
ibmcloud ce project delete --name scraper-service
```

## Estimated Costs

Code Engine pricing (as of 2026):
- **vCPU**: ~$0.04 per vCPU-hour
- **Memory**: ~$0.004 per GB-hour
- **Requests**: First 100K requests/month free

Example: 1 vCPU, 2GB RAM, running 24/7:
- Monthly cost: ~$60-70
- With min-scale 0 (scales to zero): ~$5-10/month (only when in use)

## Next Steps

1. Deploy the scraper to Code Engine
2. Get the service URL
3. Update RAG backend with the new URL
4. Test bulk ingestion from the UI
5. Monitor logs and performance