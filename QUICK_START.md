# Quick Start Guide - IBM Power RAG Demos

## For First-Time Users

### Prerequisites
- Access to IBM TechZone
- OpenShift cluster reserved (TechZone: "OpenShift on POWER10")
- `oc` CLI installed on your local machine

### 5-Minute Setup

1. **Login to OpenShift**
   ```bash
   oc login --token=<your-token> --server=<your-server>
   ```

2. **Create or switch to project**
   ```bash
   oc project llm-on-techzone
   ```

3. **Deploy Part 1 (LLM)** - Follow main README.md sections 1.1-1.5

4. **Deploy Part 2 (Milvus)** - Follow main README.md section 2.1

5. **Deploy Part 3 (Sales Manual RAG)**
   - Use OpenShift Web Console "+Add" → "Import from Git"
   - Git URL: `https://github.com/DSpurway/IBM-Power-RAG-Demos`
   - Deploy each service with these context directories:
     - `/Part3-RAG-Sales-Manual/RAG-List-Collections` → Name: `rag-list-collections`
     - `/Part3-RAG-Sales-Manual/RAG-Drop-Collection` → Name: `rag-drop-collection`
     - `/Part3-RAG-Sales-Manual/RAG-Loader` → Name: `rag-loader`
     - `/Part3-RAG-Sales-Manual/RAG-Get-Docs` → Name: `rag-get-docs`
     - `/Part3-RAG-Sales-Manual/RAG-Prompt-LLM` → Name: `rag-prompt-llm`
     - `/Part3-RAG-Sales-Manual/RAG-Webpage` → Name: `rag-webpage`

6. **Configure Services**
   ```bash
   cd Part3-RAG-Sales-Manual
   chmod +x setup-part3.sh
   ./setup-part3.sh
   ```
   - Enter your TechZone environment number (e.g., p1293)
   - Choose 'n' for CORS (wildcard is fine for demo)

7. **Access the Demo**
   - Get webpage URL: `oc get route rag-webpage`
   - Open in browser
   - Click "List Collections" to verify it works

### Using the Demo

1. **Load Sales Manuals**
   - Click buttons to load IBM Power S1012, S1014, S1022, S1022s, S1024
   - Each takes 2-5 minutes (check pod logs if timeout)

2. **Query the Data**
   - Select a server from dropdown
   - Edit question if desired
   - Click "retrieve data" button
   - Review the chunks returned

3. **Get LLM Response**
   - Click "set the prompt" to build prompt
   - Click "Send the prompt to the LLM"
   - If timeout, check `oc logs -f deployment/rag-prompt-llm`

## Common Issues

### CORS Errors
```bash
# Set CORS for all services
for service in rag-list-collections rag-drop-collection rag-loader rag-get-docs rag-prompt-llm; do
  oc set env deployment/$service CORS_ORIGIN='*'
done
```

### Service Not Found
```bash
# Check all pods are running
oc get pods -l app=sales-manual-rag-app

# Check specific deployment
oc get deployment rag-list-collections
```

### Timeout on Webpage
- This is normal for large operations
- Check pod logs: `oc logs -f deployment/rag-loader`
- The operation usually completes successfully

## Key Commands

```bash
# View all services
oc get all -l app=sales-manual-rag-app

# Check pod logs
oc logs -f deployment/rag-list-collections

# Restart a service
oc rollout restart deployment/rag-webpage

# Get route URL
oc get route rag-webpage -o jsonpath='{.spec.host}'

# Set environment variable
oc set env deployment/rag-webpage CORS_ORIGIN='*'
```

## Next Steps

- Review `IMPROVEMENTS_SUMMARY.md` for detailed changes
- Check `Part3-RAG-Sales-Manual/DEPLOYMENT_GUIDE.md` for advanced configuration
- Experiment with different questions and prompts
- Try loading your own PDF documents

## Getting Help

1. Check pod logs for errors
2. Verify environment variables are set
3. Review the DEPLOYMENT_GUIDE.md troubleshooting section
4. Contact David Spurway for assistance

---

**Tip**: The demo works best when you understand each step. Take time to review the logs and see what's happening behind the scenes!