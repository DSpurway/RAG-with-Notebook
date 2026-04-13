"""
Consolidated RAG Backend Service with ChromaDB
Combines all RAG operations into a single Flask application
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import chromadb
from chromadb.config import Settings
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain_core.load import dumps
import requests
import os
import logging

app = Flask(__name__)

# Configure CORS - allow all origins by default, can be restricted via environment variable
cors_origin = os.environ.get('CORS_ORIGIN', '*')
if cors_origin == '*':
    CORS(app)
else:
    CORS(app, origins=[cors_origin])

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Optional web scraping support - only import if available
try:
    from web_scraper import IBMDocsScraper, create_langchain_documents, IBMDocsScraperError
    WEB_SCRAPING_AVAILABLE = True
    logger.info("Web scraping module loaded successfully")
except ImportError:
    WEB_SCRAPING_AVAILABLE = False
    logger.warning("Web scraping module not available. Running in PDF-only mode.")

# Configuration from environment variables
CHROMA_PERSIST_DIR = os.environ.get('CHROMA_PERSIST_DIR', '/app/chroma_db')
LLAMA_HOST = os.environ.get('LLAMA_HOST', 'llama-service')
LLAMA_PORT = os.environ.get('LLAMA_PORT', '8080')

# PDF directory
PDF_DIR = os.environ.get('PDF_DIR', '/app/pdfs')

# Initialize ChromaDB client (lazy loading)
_chroma_client = None

def get_chroma_client():
    """Lazy load ChromaDB client"""
    global _chroma_client
    if _chroma_client is None:
        logger.info(f"Initializing ChromaDB client at {CHROMA_PERSIST_DIR}")
        _chroma_client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
        logger.info("ChromaDB client initialized")
    return _chroma_client

# Initialize embeddings model (lazy loading)
_embeddings = None

def get_embeddings():
    """Lazy load embeddings model"""
    global _embeddings
    if _embeddings is None:
        logger.info("Loading embeddings model...")
        _embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        logger.info("Embeddings model loaded")
    return _embeddings

# ============================================================================
# COLLECTION MANAGEMENT ENDPOINTS
# ============================================================================

@app.route('/api/collections', methods=['GET'])
def list_collections():
    """List all collections in ChromaDB"""
    try:
        client = get_chroma_client()
        collections = client.list_collections()
        collection_names = [col.name for col in collections]
        
        logger.info(f"Found collections: {collection_names}")
        
        return jsonify({
            'success': True,
            'collections': collection_names
        })
    except Exception as e:
        logger.error(f"Error listing collections: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/collections/<collection_name>', methods=['DELETE'])
def drop_collection(collection_name):
    """Drop a specific collection"""
    try:
        client = get_chroma_client()
        
        logger.info(f"Dropping collection: {collection_name}")
        client.delete_collection(name=collection_name)
        logger.info(f"Collection {collection_name} dropped successfully")
        
        return jsonify({
            'success': True,
            'message': f'Collection {collection_name} dropped successfully'
        })
    except Exception as e:
        logger.error(f"Error dropping collection: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# PDF LOADING ENDPOINT
# ============================================================================

@app.route('/api/load-pdf', methods=['POST'])
def load_pdf():
    """Load a PDF into the vector database"""
    try:
        data = request.get_json()
        server_name = data.get('server_name')
        collection_name = data.get('collection_name', 'sales_manuals')
        
        if not server_name:
            return jsonify({'error': 'server_name is required'}), 400
        
        # Construct PDF path
        pdf_path = os.path.join(PDF_DIR, f"{server_name}.pdf")
        
        if not os.path.exists(pdf_path):
            return jsonify({'error': f'PDF not found: {pdf_path}'}), 404
        
        logger.info(f"Loading PDF: {pdf_path}")
        
        # Load and split PDF
        loader = PyPDFLoader(pdf_path)
        docs = loader.load()
        
        text_splitter = CharacterTextSplitter(
            separator="\n",
            chunk_size=768,
            chunk_overlap=0
        )
        docs = text_splitter.split_documents(docs)
        
        logger.info(f"Split into {len(docs)} chunks")
        
        # Get embeddings
        embeddings = get_embeddings()
        
        logger.info(f"Creating/updating vector store in collection: {collection_name}")
        
        # Create or add to ChromaDB collection
        vector_store = Chroma.from_documents(
            documents=docs,
            embedding=embeddings,
            collection_name=collection_name,
            persist_directory=CHROMA_PERSIST_DIR
        )
        
        logger.info(f"Successfully loaded {server_name} into collection {collection_name}")
        
        return jsonify({
            'success': True,
            'message': f'Successfully loaded {server_name}',
            'chunks': len(docs),
            'collection': collection_name
        })
        
    except Exception as e:
        logger.error(f"Error loading PDF: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/load-url', methods=['POST'])
def load_url():
    """Load content from a web URL into the vector database"""
    if not WEB_SCRAPING_AVAILABLE:
        return jsonify({
            'error': 'Web scraping feature not available. Please use PDF loading instead.'
        }), 501
    
    try:
        data = request.get_json()
        url = data.get('url')
        collection_name = data.get('collection_name', 'web_docs')
        
        if not url:
            return jsonify({'error': 'url is required'}), 400
        
        logger.info(f"Loading content from URL: {url}")
        
        # Scrape the web page
        scraper = IBMDocsScraper()
        try:
            scraped_data = scraper.scrape_url(url)
        except IBMDocsScraperError as e:
            logger.error(f"Scraping failed: {e}")
            return jsonify({'error': f'Failed to scrape URL: {str(e)}'}), 400
        
        logger.info(f"Successfully scraped: {scraped_data['title']}")
        
        # Convert to LangChain documents
        docs = create_langchain_documents(scraped_data)
        
        # Split documents into chunks
        text_splitter = CharacterTextSplitter(
            separator="\n",
            chunk_size=768,
            chunk_overlap=100
        )
        docs = text_splitter.split_documents(docs)
        
        logger.info(f"Split into {len(docs)} chunks")
        
        # Get embeddings
        embeddings = get_embeddings()
        
        logger.info("Creating vector store...")
        vector_store = Chroma.from_documents(
            documents=docs,
            embedding=embeddings,
            collection_name=collection_name,
            persist_directory=CHROMA_PERSIST_DIR
        )
        
        logger.info(f"Successfully loaded URL into collection {collection_name}")
        
        return jsonify({
            'success': True,
            'message': 'Successfully loaded content from URL',
            'title': scraped_data['title'],
            'chunks': len(docs),
            'collection': collection_name,
            'url': url
        })
        
    except Exception as e:
        logger.error(f"Error loading URL: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/load-multiple-urls', methods=['POST'])
def load_multiple_urls():
    """Load content from multiple web URLs into the vector database"""
    if not WEB_SCRAPING_AVAILABLE:
        return jsonify({
            'error': 'Web scraping feature not available. Please use PDF loading instead.'
        }), 501
    
    try:
        data = request.get_json()
        urls = data.get('urls', [])
        collection_name = data.get('collection_name', 'web_docs')
        
        if not urls or not isinstance(urls, list):
            return jsonify({'error': 'urls array is required'}), 400
        
        logger.info(f"Loading content from {len(urls)} URLs")
        
        # Scrape all URLs
        scraper = IBMDocsScraper()
        scraped_results = scraper.scrape_multiple_urls(urls)
        
        if not scraped_results:
            return jsonify({'error': 'Failed to scrape any URLs'}), 400
        
        logger.info(f"Successfully scraped {len(scraped_results)} pages")
        
        # Convert all to LangChain documents
        all_docs = []
        for scraped_data in scraped_results:
            docs = create_langchain_documents(scraped_data)
            all_docs.extend(docs)
        
        # Split documents into chunks
        text_splitter = CharacterTextSplitter(
            separator="\n",
            chunk_size=768,
            chunk_overlap=100
        )
        all_docs = text_splitter.split_documents(all_docs)
        
        logger.info(f"Split into {len(all_docs)} total chunks")
        
        # Get embeddings
        embeddings = get_embeddings()
        
        logger.info("Creating vector store...")
        vector_store = Chroma.from_documents(
            documents=all_docs,
            embedding=embeddings,
            collection_name=collection_name,
            persist_directory=CHROMA_PERSIST_DIR
        )
        
        logger.info(f"Successfully loaded {len(scraped_results)} URLs into collection {collection_name}")
        
        titles = [result['title'] for result in scraped_results]
        
        return jsonify({
            'success': True,
            'message': f'Successfully loaded {len(scraped_results)} URLs',
            'pages_loaded': len(scraped_results),
            'total_chunks': len(all_docs),
            'collection': collection_name,
            'titles': titles
        })
        
    except Exception as e:
        logger.error(f"Error loading multiple URLs: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# SEARCH ENDPOINT
# ============================================================================

@app.route('/api/search', methods=['POST'])
def search():
    """Search for relevant documents"""
    try:
        data = request.get_json()
        question = data.get('question')
        collection_name = data.get('collection_name', 'sales_manuals')
        server_name = data.get('server_name')  # Optional filter
        k = data.get('k', 3)
        
        if not question:
            return jsonify({'error': 'question is required'}), 400
        
        logger.info(f"Searching in collection {collection_name} for: {question}")
        
        # Get embeddings
        embeddings = get_embeddings()
        
        # Connect to existing collection
        vector_store = Chroma(
            collection_name=collection_name,
            embedding_function=embeddings,
            persist_directory=CHROMA_PERSIST_DIR
        )
        
        # Perform similarity search
        if server_name:
            # Filter by server name if provided
            results = vector_store.similarity_search_with_score(
                question,
                k=k,
                filter={"source": f"{server_name}.pdf"}
            )
        else:
            results = vector_store.similarity_search_with_score(question, k=k)
        
        logger.info(f"Found {len(results)} results")
        
        # Format results
        formatted_results = []
        for doc, score in results:
            formatted_results.append({
                'content': doc.page_content,
                'metadata': doc.metadata,
                'score': float(score)
            })
        
        return jsonify({
            'success': True,
            'results': formatted_results,
            'count': len(formatted_results)
        })
        
    except Exception as e:
        logger.error(f"Error searching: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# LLM GENERATION ENDPOINT
# ============================================================================

@app.route('/api/generate', methods=['POST'])
def generate():
    """Generate response from LLM"""
    try:
        data = request.get_json()
        prompt = data.get('prompt')
        temperature = data.get('temperature', 0.1)
        n_predict = data.get('n_predict', 100)
        stream = data.get('stream', False)
        
        if not prompt:
            return jsonify({'error': 'prompt is required'}), 400
        
        logger.info(f"Generating response with temperature={temperature}, n_predict={n_predict}")
        
        # Call LLM service
        llm_url = f"http://{LLAMA_HOST}:{LLAMA_PORT}/completion"
        
        payload = {
            "prompt": prompt,
            "temperature": temperature,
            "n_predict": n_predict,
            "stream": stream
        }
        
        response = requests.post(llm_url, json=payload, timeout=60)
        response.raise_for_status()
        
        result = response.json()
        
        return jsonify({
            'success': True,
            'content': result.get('content', ''),
            'timings': result.get('timings', {})
        })
        
    except requests.exceptions.Timeout:
        logger.error("LLM request timed out")
        return jsonify({'error': 'LLM request timed out'}), 504
    except requests.exceptions.RequestException as e:
        logger.error(f"Error calling LLM: {e}")
        return jsonify({'error': f'Failed to call LLM: {str(e)}'}), 500
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    try:
        # Check ChromaDB
        client = get_chroma_client()
        client.heartbeat()  # Verify ChromaDB is responsive
        chroma_status = "connected"
    except Exception as e:
        logger.error(f"ChromaDB health check failed: {e}")
        chroma_status = "disconnected"
    
    # Check LLM service
    try:
        llm_url = f"http://{LLAMA_HOST}:{LLAMA_PORT}/health"
        response = requests.get(llm_url, timeout=5)
        llm_status = "connected" if response.status_code == 200 else "disconnected"
    except:
        llm_status = "disconnected"
    
    overall_status = "healthy" if chroma_status == "connected" else "degraded"
    
    return jsonify({
        'status': overall_status,
        'chromadb': chroma_status,
        'llm': llm_status
    }), 200 if overall_status == "healthy" else 503

# ============================================================================
# ROOT ENDPOINT
# ============================================================================

@app.route('/', methods=['GET'])
def root():
    """API documentation"""
    return jsonify({
        'service': 'RAG Backend with ChromaDB',
        'version': '2.0.0',
        'endpoints': {
            'collections': {
                'GET /api/collections': 'List all collections',
                'DELETE /api/collections/<name>': 'Drop a collection'
            },
            'documents': {
                'POST /api/load-pdf': 'Load PDF into vector database',
                'POST /api/load-url': 'Load web page into vector database',
                'POST /api/load-multiple-urls': 'Load multiple web pages',
                'POST /api/search': 'Search for relevant documents'
            },
            'generation': {
                'POST /api/generate': 'Generate LLM response'
            },
            'health': {
                'GET /health': 'Health check'
            }
        }
    })

if __name__ == '__main__':
    # Create persist directory if it doesn't exist
    os.makedirs(CHROMA_PERSIST_DIR, exist_ok=True)
    os.makedirs(PDF_DIR, exist_ok=True)
    
    logger.info(f"ChromaDB persist directory: {CHROMA_PERSIST_DIR}")
    logger.info(f"PDF directory: {PDF_DIR}")
    logger.info("Starting RAG Backend with ChromaDB...")
    
    app.run(host='0.0.0.0', port=8080, debug=False)

# Made with Bob
