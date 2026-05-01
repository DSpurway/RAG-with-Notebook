# IBM Power RAG Demos

A collection of demonstrations showcasing Retrieval Augmented Generation (RAG) on IBM Power10 systems using OpenShift.

## Overview

This repository contains three progressive demonstrations:

1. **Part 1: Deploy a Large Language Model** - Deploy TinyLlama and Granite models on Power10
2. **Part 2: RAG with Jupyter Notebook** *(Legacy - Optional)* - Vector database integration using Milvus
3. **Part 3: Production RAG with Carbon UI** *(Recommended)* - Modern web interface for IBM Power sales manual queries

## Quick Start

### Prerequisites

- Access to IBM TechZone
- OpenShift cluster on Power10 (reserve from [TechZone RAG Collection](https://techzone.ibm.com/collection/retrieval-augmented-generation-rag-on-power10))
- `oc` CLI installed on your local machine

### Recommended Demo Path

For the best experience, follow this streamlined approach:

1. **Deploy the LLM** (Part 1) - ~10 minutes
2. **Deploy the Carbon UI RAG Demo** (Part 3) - ~15 minutes
3. **Load and Query Sales Manuals** - Interactive demo

See [QUICK_START.md](QUICK_START.md) for detailed deployment steps.

## What This Demo Shows

### The Problem: LLM Hallucinations

Large Language Models can "hallucinate" - generating plausible but incorrect information. Try asking a basic LLM about specific technical details it wasn't trained on, and you'll often get confident but wrong answers.

### The Solution: Retrieval Augmented Generation (RAG)

RAG solves this by:
1. **Storing** your documents in a vector database
2. **Retrieving** relevant context when you ask a question
3. **Augmenting** the LLM prompt with accurate information
4. **Generating** responses based on your actual data

### Why IBM Power?

- **MMA Acceleration**: Power10's Matrix Math Accelerator units optimize LLM inference
- **Data Sovereignty**: Keep your data on-premises and secure
- **No Retraining Needed**: Use RAG instead of expensive model retraining
- **Production Ready**: Enterprise-grade platform for AI workloads

## Architecture

```
┌─────────────────┐
│   Carbon UI     │  Modern web interface
│   (Next.js)     │
└────────┬────────┘
         │
┌────────▼────────┐
│  RAG Backend    │  Python Flask API
│  (OpenSearch)   │  Document processing
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
┌───▼──┐  ┌──▼────┐
│Vector│  │  LLM  │
│  DB  │  │Service│
└──────┘  └───────┘
```

## Repository Structure

```
IBM-Power-RAG-Demos/
├── Part1-Deploy-LLM/          # LLM deployment (TinyLlama + Granite)
├── Part2-RAG/                 # Legacy: Jupyter Notebook demo
├── Part3-RAG-Sales-Manual/    # Production: Carbon UI + Backend
│   ├── carbon-rag-ui/         # Next.js frontend
│   ├── rag-backend/           # Python Flask backend
│   └── [microservices]/       # Supporting services
└── images/                    # Documentation screenshots
```

## Key Features

### Part 1: LLM Deployment
- Dual-model container (TinyLlama + Granite 4.0)
- Easy model switching via environment variables
- Power10 MMA acceleration enabled
- Web-based chat interface

### Part 3: Production RAG (Recommended)
- **Modern UI**: IBM Carbon Design System
- **Smart Document Processing**: Docling integration for PDFs
- **Vector Search**: OpenSearch with semantic search
- **Web Scraping**: Automated ingestion from IBM sales pages
- **Multi-Model Support**: Switch between TinyLlama and Granite
- **Production Ready**: Containerized microservices architecture

## Documentation

- [QUICK_START.md](QUICK_START.md) - Fast deployment guide
- [Part1-Deploy-LLM/README.md](Part1-Deploy-LLM/README.md) - LLM deployment details
- [Part3-RAG-Sales-Manual/DEPLOYMENT_GUIDE.md](Part3-RAG-Sales-Manual/DEPLOYMENT_GUIDE.md) - Full RAG setup
- [CARBON_UI_SUMMARY.md](CARBON_UI_SUMMARY.md) - UI features and design
- [OPENSEARCH_MIGRATION.md](OPENSEARCH_MIGRATION.md) - Vector database details

## Demo Workflow

### 1. Deploy Infrastructure
Use the automated deployment scripts or OpenShift web console to deploy:
- LLM service (with both models)
- RAG backend with OpenSearch
- Carbon UI frontend

### 2. Load Sample Data
The demo includes IBM Power server sales manuals:
- S1012, S1014, S1022, S1022s, S1024
- Automatically processed and indexed
- Web scraping capability for live data

### 3. Interactive Queries
Ask questions like:
- "What processors are available in the S1022?"
- "Compare memory options between S1014 and S1024"
- "What are the power requirements for S1012?"

The system will:
1. Search the vector database for relevant content
2. Build a context-aware prompt
3. Send to the LLM for natural language response
4. Display both the source chunks and the generated answer

## Technical Highlights

### Power10 Optimization
- Compiled with OpenBLAS for Power architecture
- MMA units accelerate matrix operations
- Optimized for both inference and vector operations

### Modern Stack
- **Frontend**: Next.js 14, React 18, IBM Carbon Design
- **Backend**: Python Flask, OpenSearch, Docling
- **LLM**: llama.cpp with Power10 optimizations
- **Deployment**: OpenShift containers, automated scripts

### Enterprise Features
- CORS configuration for secure access
- Environment-based configuration
- Comprehensive logging and monitoring
- Scalable microservices architecture

## Getting Started

1. **Reserve OpenShift Environment** from IBM TechZone
2. **Clone this repository** to your local machine
3. **Follow [QUICK_START.md](QUICK_START.md)** for deployment
4. **Access the Carbon UI** and start querying!

## Migration from Legacy Version

If you're using the older `RAG-with-Notebook` repository:
- The legacy version remains available at the original repository
- This version focuses on production-ready Carbon UI
- Part 2 (Jupyter Notebook) is still included but optional
- All new features and improvements are in Part 3

## Support and Contributions

This is a demonstration project for IBM Power10 capabilities. For questions or issues:
- Review the documentation in each Part's directory
- Check the troubleshooting sections in deployment guides
- Contact: David Spurway

## License

See [LICENSE](LICENSE) file for details.

## Acknowledgments

- Original concept and implementation: David Spurway
- IBM Carbon Design System
- llama.cpp community
- OpenSearch project
- Docling document processing

---

**Ready to see RAG in action on Power10?** Start with [QUICK_START.md](QUICK_START.md)!
