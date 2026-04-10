# Carbon RAG UI - Retrieval Augmented Generation Demo

A modern, professional UI for the RAG-with-Notebook demo built with Next.js and IBM's Carbon Design System.

## Features

- **Modern Carbon UI**: Professional interface using IBM Carbon Design System
- **Tabbed Interface**: 
  - About RAG: Educational content about RAG technology
  - Part 2: Harry Potter RAG demo (basic RAG with fiction)
  - Part 3: Sales Manual RAG demo (enterprise RAG with technical docs)
- **Environment-Based Configuration**: All service URLs configurable via environment variables
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Real-time Feedback**: Loading states, error handling, and success notifications

## Getting Started

### Prerequisites

- Node.js 18+ 
- npm or yarn
- Running RAG backend services (Milvus, LLM, Part 3 services)

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
# Milvus Configuration
NEXT_PUBLIC_MILVUS_HOST=milvus-service
NEXT_PUBLIC_MILVUS_PORT=19530

# LLM Configuration
NEXT_PUBLIC_LLAMA_HOST=llama-service
NEXT_PUBLIC_LLAMA_PORT=8080

# Part 3 Service URLs (Sales Manual RAG)
NEXT_PUBLIC_LIST_COLLECTIONS_URL=https://rag-list-collections-llm-on-techzone.apps.pXXXX.cecc.ihost.com
NEXT_PUBLIC_DROP_COLLECTION_URL=https://rag-drop-collection-llm-on-techzone.apps.pXXXX.cecc.ihost.com
NEXT_PUBLIC_LOADER_URL=https://rag-loader-llm-on-techzone.apps.pXXXX.cecc.ihost.com
NEXT_PUBLIC_GET_DOCS_URL=https://rag-get-docs-llm-on-techzone.apps.pXXXX.cecc.ihost.com
NEXT_PUBLIC_PROMPT_LLM_URL=https://rag-prompt-llm-llm-on-techzone.apps.pXXXX.cecc.ihost.com
```

Replace `pXXXX` with your TechZone environment number.

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
  -e NEXT_PUBLIC_MILVUS_HOST=milvus-service \
  -e NEXT_PUBLIC_LLAMA_HOST=llama-service \
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

# Set environment variables
oc set env deployment/carbon-rag-ui \
  NEXT_PUBLIC_LIST_COLLECTIONS_URL=https://rag-list-collections-llm-on-techzone.apps.pXXXX.cecc.ihost.com \
  NEXT_PUBLIC_DROP_COLLECTION_URL=https://rag-drop-collection-llm-on-techzone.apps.pXXXX.cecc.ihost.com \
  NEXT_PUBLIC_LOADER_URL=https://rag-loader-llm-on-techzone.apps.pXXXX.cecc.ihost.com \
  NEXT_PUBLIC_GET_DOCS_URL=https://rag-get-docs-llm-on-techzone.apps.pXXXX.cecc.ihost.com \
  NEXT_PUBLIC_PROMPT_LLM_URL=https://rag-prompt-llm-llm-on-techzone.apps.pXXXX.cecc.ihost.com
```

## Technologies

- **Next.js 14**: React framework with App Router
- **Carbon Design System**: IBM's open-source design system
- **React 18**: UI library
- **SCSS**: Styling with Carbon's SCSS utilities

## Features in Detail

### Dynamic Configuration
All service URLs are configurable via environment variables, making it easy to deploy across different environments without code changes.

### Error Handling
Comprehensive error handling with user-friendly messages and guidance to check pod logs when operations timeout.

### Loading States
Visual feedback during all async operations with loading indicators and disabled buttons.

### Responsive Design
Fully responsive layout that works on all screen sizes using Carbon's grid system.

### Accessibility
Built with Carbon components that follow WCAG accessibility guidelines.

## Troubleshooting

### Services Not Responding
- Check that all backend services are running: `oc get pods`
- Verify environment variables are set correctly
- Check pod logs: `oc logs -f deployment/service-name`

### CORS Errors
- Ensure CORS_ORIGIN is set on backend services
- Verify service URLs are correct in environment variables

### Timeout Issues
- Large PDF loading may timeout - check pod logs for actual status
- LLM responses may take time - results appear in pod logs even if UI times out

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