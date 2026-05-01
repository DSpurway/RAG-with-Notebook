# Carbon RAG UI - Retrieval Augmented Generation Demo

A modern, professional UI for the RAG-with-Notebook demo built with Next.js and IBM's Carbon Design System.

## Features

- **Modern Carbon UI**: Professional interface using IBM Carbon Design System
- **Tabbed Interface**:
  - About RAG: Educational content about RAG technology
  - Part 2: Harry Potter RAG demo (basic RAG with fiction)
  - Part 3: Sales Manual RAG demo (enterprise RAG with technical docs)
- **Unified Backend**: Single ChromaDB-based backend service (simplified from 5 microservices)
- **Environment-Based Configuration**: Backend URL configurable via environment variable
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Real-time Feedback**: Loading states, error handling, and success notifications

## Architecture

This UI now connects to a **unified RAG backend** powered by ChromaDB, replacing the previous architecture of 5 separate microservices (Milvus, etcd, MinIO, loader, search, prompt services).

### Backend API Endpoints

- `GET /api/collections` - List available collections
- `POST /api/load-pdf` - Load PDF into collection
- `POST /api/search` - Search for relevant documents
- `POST /api/generate` - Generate LLM response

## Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn
- Running RAG backend service (ChromaDB-based unified backend)

### Installation

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Start production server
npm start
```

Open [http://localhost:3000](http://localhost:3000) to view the application.

## Configuration

Create a `.env.local` file in the root directory:

```env
# Unified RAG Backend (ChromaDB)
NEXT_PUBLIC_RAG_BACKEND_URL=http://rag-backend:8080

# For OpenShift deployment with route:
# NEXT_PUBLIC_RAG_BACKEND_URL=https://rag-backend-llm-on-techzone.apps.pXXXX.cecc.ihost.com
```

Replace `pXXXX` with your TechZone environment number if deploying to OpenShift.

### Default Configuration

If no environment variable is set, the UI defaults to `http://localhost:8080` for local development.

## Project Structure

```
carbon-rag-ui/
├── src/
│   ├── app/
│   │   ├── home/          # Landing page
│   │   ├── rag/           # Main RAG demo page
│   │   ├── globals.scss   # Global styles
│   │   ├── layout.js      # Root layout
│   │   └── providers.js   # Carbon providers
│   └── components/
│       └── TutorialHeader/ # Navigation header
├── public/                # Static assets
├── package.json
└── README.md
```

## Usage

### Part 2: Harry Potter RAG

1. Navigate to the "Part 2: Harry Potter" tab
2. Enter a question about Harry Potter
3. Click "Retrieve Relevant Passages" to get context from the book
4. Review the retrieved passages
5. Click "Build Prompt" to create the LLM prompt
6. Click "Send to LLM" to get the answer

### Part 3: Sales Manual RAG

1. Navigate to the "Part 3: Sales Manuals" tab
2. Load IBM Power Sales Manuals by clicking the server buttons
3. Select a server from the dropdown
4. Enter your question
5. Click "Retrieve Relevant Passages"
6. Review the retrieved technical specifications
7. Click "Build Prompt" and then "Send to LLM"

## Deployment

### Docker

```bash
# Build Docker image
docker build -t carbon-rag-ui .

# Run container
docker run -p 3000:3000 \
  -e NEXT_PUBLIC_RAG_BACKEND_URL=http://rag-backend:8080 \
  carbon-rag-ui
```

### OpenShift

Deploy using the provided Dockerfile:

```bash
# From OpenShift Web Console:
# 1. +Add -> Import from Git
# 2. Git URL: https://github.com/DSpurway/RAG-with-Notebook
# 3. Context dir: /carbon-rag-ui
# 4. Name: carbon-rag-ui
# 5. Create

# Set environment variable for the unified backend
oc set env deployment/carbon-rag-ui \
  NEXT_PUBLIC_RAG_BACKEND_URL=https://rag-backend-llm-on-techzone.apps.pXXXX.cecc.ihost.com

# Or use internal service name if in same namespace
oc set env deployment/carbon-rag-ui \
  NEXT_PUBLIC_RAG_BACKEND_URL=http://rag-backend:8080
```

## Technologies

- **Next.js 14**: React framework with App Router
- **Carbon Design System**: IBM's open-source design system
- **React 18**: UI library
- **SCSS**: Styling with Carbon's SCSS utilities

## Features in Detail

### Simplified Configuration
Single backend URL configuration (down from 5+ service URLs), making deployment and maintenance much simpler.

### ChromaDB Backend
Unified backend service using ChromaDB for vector storage, replacing the previous Milvus + etcd + MinIO architecture.

### Error Handling
Comprehensive error handling with user-friendly messages and guidance to check pod logs when operations timeout.

### Loading States
Visual feedback during all async operations with loading indicators and disabled buttons.

### Responsive Design
Fully responsive layout that works on all screen sizes using Carbon's grid system.

### Accessibility
Built with Carbon components that follow WCAG accessibility guidelines.

## Troubleshooting

### Backend Not Responding
- Check that the RAG backend service is running: `oc get pods | grep rag-backend`
- Verify environment variable is set correctly: `oc get deployment carbon-rag-ui -o jsonpath='{.spec.template.spec.containers[0].env}'`
- Check backend logs: `oc logs -f deployment/rag-backend`

### CORS Errors
- Ensure the backend has CORS enabled for your UI origin
- Verify the backend URL is correct in environment variables

### Timeout Issues
- Large PDF loading may timeout - check backend pod logs for actual status
- LLM responses may take time - results appear in backend logs even if UI times out
- ChromaDB initialization on first request may be slow

### Collection Not Found
- Ensure PDFs are loaded before querying
- Check collection names match (lowercase with hyphens, e.g., `power-s1014` not `Power_S1014`)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is part of the RAG-with-Notebook demo and follows the same license.

## Support

For issues or questions:
- Check the main RAG-with-Notebook README
- Review the DEPLOYMENT_GUIDE.md
- Contact the EMEA AI Squad

---

Built with ❤️ by the EMEA AI on IBM Power Squad