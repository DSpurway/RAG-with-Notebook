"""
Consolidated RAG Backend Service
Combines all RAG operations into a single Flask application
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from pymilvus import connections, utility
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Milvus
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain_core.load import dumps
import requests
import os
import logging
from web_scraper import IBMDocsScraper, create_langchain_documents, IBMDocsScraperError

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

# Configuration from environment variables
MILVUS_HOST = os.environ.get('MILVUS_HOST', 'milvus-service')
MILVUS_PORT = os.environ.get('MILVUS_PORT', '19530')
LLAMA_HOST = os.environ.get('LLAMA_HOST', 'llama-service')
LLAMA_PORT = os.environ.get('LLAMA_PORT', '8080')

# PDF directory
PDF_DIR = os.environ.get('PDF_DIR', '/app/pdfs')

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

def connect_milvus():
    """Connect to Milvus database"""
    try:
        connections.connect(host=MILVUS_HOST, port=MILVUS_PORT)
        logger.info(f"Connected to Milvus at {MILVUS_HOST}:{MILVUS_PORT}")
        return True
    except Exception as e:
        logger.error(f"Failed to connect to Milvus: {e}")
        return False

# ============================================================================
# COLLECTION MANAGEMENT ENDPOINTS
# ============================================================================

@app.route('/api/collections', methods=['GET'])
def list_collections():
    """List all collections in Milvus"""
    try:
        if not connect_milvus():
            return jsonify({'error': 'Failed to connect to Milvus'}), 500
        
        collections = utility.list_collections()
        logger.info(f"Found collections: {collections}")
        
        return jsonify({
            'success': True,
            'collections': collections
        })
    except Exception as e:
        logger.error(f"Error listing collections: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/collections/<collection_name>', methods=['DELETE'])
def drop_collection(collection_name):
    """Drop a specific collection"""
    try:
        if not connect_milvus():
            return jsonify({'error': 'Failed to connect to Milvus'}), 500
        
        logger.info(f"Dropping collection: {collection_name}")
        utility.drop_collection(collection_name)
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
        
        if not connect_milvus():
            return jsonify({'error': 'Failed to connect to Milvus'}), 500
        
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
        
        # Get embeddings and create vector store
        embeddings = get_embeddings()
        
        logger.info("Creating vector store...")
        vector_store = Milvus.from_documents(
            docs,
            embedding=embeddings,
            collection_name=collection_name,
            connection_args={"host": MILVUS_HOST, "port": MILVUS_PORT}
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
    try:
        data = request.get_json()
        url = data.get('url')
        collection_name = data.get('collection_name', 'web_docs')
        
        if not url:
            return jsonify({'error': 'url is required'}), 400
        
        if not connect_milvus():
            return jsonify({'error': 'Failed to connect to Milvus'}), 500
        
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
        
        # Get embeddings and create vector store
        embeddings = get_embeddings()
        
        logger.info("Creating vector store...")
        vector_store = Milvus.from_documents(
            docs,
            embedding=embeddings,
            collection_name=collection_name,
            connection_args={"host": MILVUS_HOST, "port": MILVUS_PORT}
        )
        
        logger.info(f"Successfully loaded content from {url} into collection {collection_name}")
        
        return jsonify({
            'success': True,
            'message': f'Successfully loaded content from URL',
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
    try:
        data = request.get_json()
        urls = data.get('urls', [])
        collection_name = data.get('collection_name', 'web_docs')
        
        if not urls or not isinstance(urls, list):
            return jsonify({'error': 'urls array is required'}), 400
        
        if not connect_milvus():
            return jsonify({'error': 'Failed to connect to Milvus'}), 500
        
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
        
        # Get embeddings and create vector store
        embeddings = get_embeddings()
        
        logger.info("Creating vector store...")
        vector_store = Milvus.from_documents(
            all_docs,
            embedding=embeddings,
            collection_name=collection_name,
            connection_args={"host": MILVUS_HOST, "port": MILVUS_PORT}
        )
        
        logger.info(f"Successfully loaded {len(scraped_results)} URLs into collection {collection_name}")
        
        return jsonify({
            'success': True,
            'message': f'Successfully loaded {len(scraped_results)} URLs',
            'pages_loaded': len(scraped_results),
            'total_chunks': len(all_docs),
            'collection': collection_name,
            'titles': [r['title'] for r in scraped_results]
        })
        
    except Exception as e:
        logger.error(f"Error loading multiple URLs: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# SEARCH ENDPOINT
# ============================================================================

@app.route('/api/search', methods=['POST'])
def search_documents():
    """Search for relevant documents"""
    try:
        data = request.get_json()
        question = data.get('question')
        collection_name = data.get('collection_name', 'demo')
        server_name = data.get('server_name')  # Optional, for filtering
        k = data.get('k', 3)
        
        if not question:
            return jsonify({'error': 'question is required'}), 400
        
        if not connect_milvus():
            return jsonify({'error': 'Failed to connect to Milvus'}), 500
        
        logger.info(f"Searching in collection {collection_name} for: {question}")
        
        # Get embeddings and connect to vector store
        embeddings = get_embeddings()
        
        vector_store = Milvus(
            embedding_function=embeddings,
            collection_name=collection_name,
            connection_args={"host": MILVUS_HOST, "port": MILVUS_PORT}
        )
        
        # Build filter expression if server_name provided
        expr = None
        if server_name:
            pdf_filename = f"{server_name}.pdf"
            expr = f"source == '{pdf_filename}'"
            logger.info(f"Filtering by source: {pdf_filename}")
        
        # Perform search
        if expr:
            docs = vector_store.similarity_search_with_score(question, k=k, expr=expr)
        else:
            docs = vector_store.similarity_search_with_score(question, k=k)
        
        logger.info(f"Found {len(docs)} relevant documents")
        
        # Format results
        results = []
        for doc, score in docs:
            results.append({
                'content': doc.page_content,
                'metadata': doc.metadata,
                'score': float(score)
            })
        
        return jsonify({
            'success': True,
            'results': results,
            'count': len(results)
        })
        
    except Exception as e:
        logger.error(f"Error searching documents: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# LLM GENERATION ENDPOINT
# ============================================================================

@app.route('/api/generate', methods=['POST'])
def generate_response():
    """Generate response from LLM"""
    try:
        data = request.get_json()
        prompt = data.get('prompt')
        temperature = data.get('temperature', 0.1)
        n_predict = data.get('n_predict', 100)
        stream = data.get('stream', False)
        
        if not prompt:
            return jsonify({'error': 'prompt is required'}), 400
        
        logger.info(f"Generating response for prompt (length: {len(prompt)})")
        
        # Call LLM service
        llm_url = f'http://{LLAMA_HOST}:{LLAMA_PORT}/completion'
        
        payload = {
            'prompt': prompt,
            'temperature': temperature,
            'n_predict': n_predict,
            'stream': stream
        }
        
        response = requests.post(llm_url, json=payload, timeout=60)
        response.raise_for_status()
        
        result = response.json()
        
        logger.info("Successfully generated response")
        
        return jsonify({
            'success': True,
            'content': result.get('content', ''),
            'timings': result.get('timings', {})
        })
        
    except requests.exceptions.Timeout:
        logger.error("LLM request timed out")
        return jsonify({'error': 'Request timed out. Check LLM service logs.'}), 504
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    health_status = {
        'status': 'healthy',
        'milvus': 'unknown',
        'llm': 'unknown'
    }
    
    # Check Milvus connection
    try:
        if connect_milvus():
            health_status['milvus'] = 'connected'
        else:
            health_status['milvus'] = 'disconnected'
            health_status['status'] = 'degraded'
    except Exception as e:
        health_status['milvus'] = f'error: {str(e)}'
        health_status['status'] = 'degraded'
    
    # Check LLM service
    try:
        llm_url = f'http://{LLAMA_HOST}:{LLAMA_PORT}/health'
        response = requests.get(llm_url, timeout=5)
        if response.status_code == 200:
            health_status['llm'] = 'connected'
        else:
            health_status['llm'] = 'disconnected'
            health_status['status'] = 'degraded'
    except Exception as e:
        health_status['llm'] = f'error: {str(e)}'
        health_status['status'] = 'degraded'
    
    status_code = 200 if health_status['status'] == 'healthy' else 503
    return jsonify(health_status), status_code

@app.route('/', methods=['GET'])
def index():
    """Root endpoint"""
    return jsonify({
        'service': 'RAG Backend API',
        'version': '1.1.0',
        'endpoints': {
            'collections': {
                'GET /api/collections': 'List all collections',
                'DELETE /api/collections/<name>': 'Drop a collection'
            },
            'documents': {
                'POST /api/load-pdf': 'Load PDF into vector database',
                'POST /api/load-url': 'Load web page content into vector database',
                'POST /api/load-multiple-urls': 'Load multiple web pages into vector database',
                'POST /api/search': 'Search for relevant documents'
            },
            'generation': {
                'POST /api/generate': 'Generate response from LLM'
            },
            'health': {
                'GET /health': 'Health check'
            }
        }
    })

if __name__ == '__main__':
    # Create PDF directory if it doesn't exist
    os.makedirs(PDF_DIR, exist_ok=True)
    
    logger.info("Starting RAG Backend Service")
    logger.info(f"Milvus: {MILVUS_HOST}:{MILVUS_PORT}")
    logger.info(f"LLM: {LLAMA_HOST}:{LLAMA_PORT}")
    logger.info(f"PDF Directory: {PDF_DIR}")
    
    app.run(host='0.0.0.0', port=8080, debug=False)

# Made with Bob
