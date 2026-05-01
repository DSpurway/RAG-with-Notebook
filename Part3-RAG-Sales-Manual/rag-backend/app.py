"""
Consolidated RAG Backend Service with OpenSearch
Adapted from IBM project-ai-services implementation
"""

from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import os
import logging
import hashlib
import numpy as np
import json
from datetime import datetime
from opensearchpy import OpenSearch, helpers
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import CharacterTextSplitter
import requests

from docling_config import (
    USE_DOCLING,
    DOCLING_CHUNK_SIZE,
    DOCLING_CHUNK_OVERLAP,
    PDF_CHUNK_SIZE,
    docling_config_dict,
)

app = Flask(__name__)

# Configure CORS
cors_origin = os.environ.get('CORS_ORIGIN', '*')
if cors_origin == '*':
    CORS(app)
else:
    CORS(app, origins=[cors_origin])

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Optional web scraping support
try:
    from web_scraper import IBMDocsScraper, create_langchain_documents, IBMDocsScraperError
    WEB_SCRAPING_AVAILABLE = True
    logger.info("Web scraping module loaded successfully")
except ImportError:
    WEB_SCRAPING_AVAILABLE = False
    logger.warning("Web scraping module not available. Running in PDF-only mode.")

# Configuration from environment variables
OPENSEARCH_HOST = os.environ.get('OPENSEARCH_HOST', 'opensearch-service')
OPENSEARCH_PORT = int(os.environ.get('OPENSEARCH_PORT', '9200'))
OPENSEARCH_USERNAME = os.environ.get('OPENSEARCH_USERNAME', 'admin')
OPENSEARCH_PASSWORD = os.environ.get('OPENSEARCH_PASSWORD', 'admin')
OPENSEARCH_DB_PREFIX = os.environ.get('OPENSEARCH_DB_PREFIX', 'rag').lower()
OPENSEARCH_NUM_SHARDS = int(os.environ.get('OPENSEARCH_NUM_SHARDS', '1'))
OPENSEARCH_USE_SSL = os.environ.get('OPENSEARCH_USE_SSL', 'false').lower() == 'true'

# LLM Service Configuration
# Granite service (for RAG - Part 3)
GRANITE_HOST = os.environ.get('GRANITE_HOST', os.environ.get('LLAMA_HOST', 'granite-llama-service'))
GRANITE_PORT = os.environ.get('GRANITE_PORT', os.environ.get('LLAMA_PORT', '8080'))

# TinyLlama service (for Part 1 - demonstrates hallucinations)
TINYLLAMA_HOST = os.environ.get('TINYLLAMA_HOST', 'tinyllama-service')
TINYLLAMA_PORT = os.environ.get('TINYLLAMA_PORT', '8080')

# Legacy support - default to Granite
LLAMA_HOST = GRANITE_HOST
LLAMA_PORT = GRANITE_PORT

PDF_DIR = os.environ.get('PDF_DIR', '/app/pdfs')

# Initialize OpenSearch client (lazy loading)
_opensearch_client = None

def get_opensearch_client():
    """Lazy load OpenSearch client"""
    global _opensearch_client
    if _opensearch_client is None:
        logger.info(f"Initializing OpenSearch client at {OPENSEARCH_HOST}:{OPENSEARCH_PORT} (SSL: {OPENSEARCH_USE_SSL})")
        _opensearch_client = OpenSearch(
            hosts=[{'host': OPENSEARCH_HOST, 'port': OPENSEARCH_PORT}],
            http_compress=True,
            use_ssl=OPENSEARCH_USE_SSL,
            http_auth=(OPENSEARCH_USERNAME, OPENSEARCH_PASSWORD) if OPENSEARCH_USE_SSL else None,
            verify_certs=False,
            ssl_show_warn=False
        )
        logger.info("OpenSearch client initialized successfully")
        _create_hybrid_pipeline()
    return _opensearch_client

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

def _generate_index_name(collection_name):
    """Generate OpenSearch index name from collection name"""
    hash_part = hashlib.md5(collection_name.encode()).hexdigest()
    return f"{OPENSEARCH_DB_PREFIX}_{hash_part}"

def _create_hybrid_pipeline():
    """Create hybrid search pipeline for combining dense and sparse results"""
    client = get_opensearch_client()
    pipeline_body = {
        "description": "Post-processor for hybrid search",
        "phase_results_processors": [
            {
                "normalization-processor": {
                    "normalization": {"technique": "min_max"},
                    "combination": {
                        "technique": "arithmetic_mean",
                        "parameters": {
                            "weights": [0.3, 0.7]  # Semantic heavy weights
                        }
                    }
                }
            }
        ]
    }
    try:
        client.search_pipeline.put(id="hybrid_pipeline", body=pipeline_body)
        logger.info("Hybrid search pipeline created successfully")
    except Exception as e:
        logger.warning(f"Hybrid pipeline may already exist: {e}")

def _setup_index(index_name, dim=384):
    """Setup OpenSearch index with k-NN configuration"""
    client = get_opensearch_client()
    
    if client.indices.exists(index=index_name):
        logger.info(f"Index {index_name} already exists")
        return
    
    logger.info(f"Creating new index {index_name} with dimension {dim}")
    
    index_body = {
        "settings": {
            "index": {
                "knn": True,
                "knn.algo_param.ef_search": 100,
                "number_of_shards": OPENSEARCH_NUM_SHARDS,
                'auto_expand_replicas': '0-all'
            }
        },
        "mappings": {
            "properties": {
                "chunk_id": {"type": "long"},
                "embedding": {
                    "type": "knn_vector",
                    "dimension": dim,
                    "method": {
                        "name": "hnsw",
                        "space_type": "cosinesimil",
                        "engine": "lucene",
                        "parameters": {
                            "ef_construction": 128,
                            "m": 24
                        }
                    }
                },
                "text": {
                    "type": "text",
                    "analyzer": "standard"
                },
                "metadata": {
                    "dynamic": "true",
                    "properties": {
                        "filename": {"type": "keyword"},
                        "doc_id": {"type": "keyword"},
                        "source": {"type": "keyword"},
                        "page_number": {"type": "integer"},
                        "chunk_index": {"type": "integer"},
                        "created_at": {"type": "date"},
                        "chapter": {"type": "text"},
                        "section": {"type": "text"},
                        "subsection": {"type": "text"},
                        "subsubsection": {"type": "text"},
                        "type": {"type": "keyword"},
                        "part_index": {"type": "integer"},
                        "processing_method": {"type": "keyword"}
                    }
                }
            }
        }
    }
    
    try:
        client.indices.create(index=index_name, body=index_body)
        logger.info(f"Index {index_name} created successfully")
    except Exception as e:
        logger.error(f"Failed to create index {index_name}: {e}")
        raise

def generate_chunk_id(doc_id, page_content):
    """Generate deterministic chunk ID"""
    base = f"{doc_id}||{page_content}"
    hash_digest = hashlib.md5(base.encode("utf-8")).hexdigest()
    chunk_int = int(hash_digest[:16], 16)
    chunk_id = chunk_int % (2**63)
    return np.int64(chunk_id)

# ============================================================================
# COLLECTION MANAGEMENT ENDPOINTS
# ============================================================================

@app.route('/api/collections', methods=['GET'])
def list_collections():
    """List all collections (OpenSearch indices)"""
    try:
        client = get_opensearch_client()
        indices = client.indices.get(index=f"{OPENSEARCH_DB_PREFIX}_*")
        
        # Extract collection names from index names
        collection_names = []
        for index_name in indices.keys():
            # Remove prefix and hash to get original name (we'll just use the index name)
            collection_names.append(index_name)
        
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
    """Drop a specific collection (delete OpenSearch index)"""
    try:
        client = get_opensearch_client()
        index_name = _generate_index_name(collection_name)
        
        logger.info(f"Dropping collection: {collection_name} (index: {index_name})")
        
        if client.indices.exists(index=index_name):
            client.indices.delete(index=index_name)
            logger.info(f"Collection {collection_name} dropped successfully")
            return jsonify({
                'success': True,
                'message': f'Collection {collection_name} dropped successfully'
            })
        else:
            return jsonify({
                'success': False,
                'message': f'Collection {collection_name} does not exist'
            }), 404
            
    except Exception as e:
        logger.error(f"Error dropping collection: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# PDF LOADING ENDPOINT
# ============================================================================

@app.route('/api/load-pdf', methods=['POST'])
def load_pdf():
    """Load a PDF into OpenSearch"""
    try:
        data = request.get_json()
        server_name = data.get('server_name')
        collection_name = data.get('collection_name', 'sales_manuals')

        if not server_name:
            return jsonify({'error': 'server_name is required'}), 400

        pdf_path = os.path.join(PDF_DIR, f"{server_name}.pdf")

        if not os.path.exists(pdf_path):
            return jsonify({'error': f'PDF not found: {pdf_path}'}), 404

        logger.info(f"Loading PDF: {pdf_path}")
        logger.info(f"Docling configuration: {docling_config_dict()}")

        processing_method = 'pypdf'
        processed_chunks = []

        if USE_DOCLING:
            try:
                from docling_converter import convert_pdf_chunked
                from hierarchical_chunker import chunk_with_hierarchy

                logger.info("USE_DOCLING enabled. Processing with Docling.")
                docling_doc = convert_pdf_chunked(pdf_path, chunk_size=PDF_CHUNK_SIZE)
                processed_chunks = chunk_with_hierarchy(
                    docling_doc,
                    max_tokens=DOCLING_CHUNK_SIZE,
                    overlap=DOCLING_CHUNK_OVERLAP
                )
                processing_method = 'docling'
            except Exception as docling_error:
                logger.exception(
                    f"Docling conversion failed for {pdf_path}. Falling back to PyPDF. Error: {docling_error}"
                )

        if not processed_chunks:
            logger.info("Processing PDF with PyPDF fallback.")
            loader = PyPDFLoader(pdf_path)
            docs = loader.load()

            text_splitter = CharacterTextSplitter(
                separator="\n",
                chunk_size=DOCLING_CHUNK_SIZE,
                chunk_overlap=0
            )
            docs = text_splitter.split_documents(docs)

            for i, doc in enumerate(docs):
                processed_chunks.append({
                    "text": doc.page_content,
                    "metadata": {
                        "filename": f"{server_name}.pdf",
                        "doc_id": server_name,
                        "source": doc.metadata.get('source', ''),
                        "page_number": doc.metadata.get('page', i),
                        "chunk_index": i,
                        "created_at": datetime.utcnow().isoformat(),
                        "chapter": None,
                        "section": None,
                        "subsection": None,
                        "subsubsection": None,
                        "type": "text",
                        "part_index": 0,
                        "processing_method": "pypdf"
                    }
                })

        logger.info(f"Prepared {len(processed_chunks)} chunks using {processing_method}")

        embeddings = get_embeddings()
        index_name = _generate_index_name(collection_name)
        _setup_index(index_name)

        client = get_opensearch_client()
        actions = []

        for i, chunk in enumerate(processed_chunks):
            page_content = chunk.get("text", "")
            if not page_content.strip():
                continue

            doc_id = server_name
            chunk_id = generate_chunk_id(doc_id, page_content)
            embedding = embeddings.embed_query(page_content)

            chunk_metadata = chunk.get("metadata", {})
            metadata = {
                "filename": chunk_metadata.get("filename", f"{server_name}.pdf"),
                "doc_id": chunk_metadata.get("doc_id", doc_id),
                "source": chunk_metadata.get("source", processing_method),
                "page_number": chunk_metadata.get("page_number", i),
                "chunk_index": i,
                "created_at": chunk_metadata.get("created_at", datetime.utcnow().isoformat()),
                "chapter": chunk_metadata.get("chapter"),
                "section": chunk_metadata.get("section"),
                "subsection": chunk_metadata.get("subsection"),
                "subsubsection": chunk_metadata.get("subsubsection"),
                "type": chunk_metadata.get("type", "text"),
                "part_index": chunk_metadata.get("part_index", 0),
                "processing_method": processing_method
            }

            actions.append({
                "_index": index_name,
                "_id": str(chunk_id),
                "_source": {
                    "chunk_id": chunk_id,
                    "embedding": embedding,
                    "text": page_content,
                    "metadata": metadata
                }
            })

        success_count, errors = helpers.bulk(
            client,
            actions,
            stats_only=False,
            raise_on_error=False,
            refresh=True
        )

        if errors:
            logger.error(f"Some chunks failed to insert: {len(errors)} errors")
            return jsonify({
                'success': False,
                'error': 'Some chunks failed to insert',
                'chunks_inserted': success_count,
                'chunks_failed': len(errors),
                'method': processing_method
            }), 500

        logger.info(f"Successfully loaded {server_name} into collection {collection_name}")

        return jsonify({
            'success': True,
            'message': f'Successfully loaded {server_name}',
            'chunks': len(actions),
            'collection': collection_name,
            'method': processing_method
        })

    except Exception as e:
        logger.error(f"Error loading PDF: {e}")
        return jsonify({'error': str(e)}), 500
@app.route('/api/load-pdf-url', methods=['POST'])
def load_pdf_url():
    """Load a PDF from a URL into OpenSearch using simple PyPDF approach"""
    try:
        data = request.get_json()
        pdf_url = data.get('pdf_url')
        collection_name = data.get('collection_name', 'demo')
        chunk_size = data.get('chunk_size', 768)
        
        if not pdf_url:
            return jsonify({'error': 'pdf_url is required'}), 400
        
        logger.info(f"Downloading PDF from URL: {pdf_url}")
        
        # Download PDF to temporary file
        import tempfile
        response = requests.get(pdf_url, timeout=60)
        response.raise_for_status()
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(response.content)
            tmp_pdf_path = tmp_file.name
        
        try:
            logger.info(f"Loading PDF with PyPDFLoader: {tmp_pdf_path}")
            loader = PyPDFLoader(tmp_pdf_path)
            docs = loader.load()
            
            # Split documents into chunks (matching notebook approach)
            text_splitter = CharacterTextSplitter(
                separator="\n",
                chunk_size=chunk_size,
                chunk_overlap=0
            )
            docs = text_splitter.split_documents(docs)
            
            logger.info(f"Split into {len(docs)} chunks")
            
            # Get embeddings
            embeddings = get_embeddings()
            index_name = _generate_index_name(collection_name)
            _setup_index(index_name)
            
            client = get_opensearch_client()
            actions = []
            
            for i, doc in enumerate(docs):
                page_content = doc.page_content
                if not page_content.strip():
                    continue
                
                chunk_id = generate_chunk_id(collection_name, page_content)
                embedding = embeddings.embed_query(page_content)
                
                metadata = {
                    "filename": pdf_url.split('/')[-1],
                    "doc_id": collection_name,
                    "source": pdf_url,
                    "page_number": doc.metadata.get('page', i),
                    "chunk_index": i,
                    "created_at": datetime.utcnow().isoformat(),
                    "type": "text",
                    "processing_method": "pypdf"
                }
                
                actions.append({
                    "_index": index_name,
                    "_id": str(chunk_id),
                    "_source": {
                        "chunk_id": chunk_id,
                        "embedding": embedding,
                        "text": page_content,
                        "metadata": metadata
                    }
                })
            
            success_count, errors = helpers.bulk(
                client,
                actions,
                stats_only=False,
                raise_on_error=False,
                refresh=True
            )
            
            if errors:
                logger.error(f"Some chunks failed to insert: {len(errors)} errors")
                return jsonify({
                    'success': False,
                    'error': 'Some chunks failed to insert',
                    'chunks_inserted': success_count,
                    'chunks_failed': len(errors)
                }), 500
            
            logger.info(f"Successfully loaded PDF from URL into collection {collection_name}")
            
            return jsonify({
                'success': True,
                'message': f'Successfully loaded PDF from URL',
                'chunks': len(actions),
                'collection': collection_name,
                'url': pdf_url
            })
            
        finally:
            # Clean up temporary file
            os.unlink(tmp_pdf_path)
    
    except Exception as e:
        logger.error(f"Error loading PDF from URL: {e}")
        return jsonify({'error': str(e)}), 500


# ============================================================================
# SEARCH ENDPOINT
# ============================================================================

@app.route('/api/search', methods=['POST'])
def search():
    """Search for relevant documents using hybrid search"""
    try:
        data = request.get_json()
        question = data.get('question')
        collection_name = data.get('collection_name', 'sales_manuals')
        k = data.get('k', 3)
        mode = data.get('mode', 'hybrid')  # dense, sparse, or hybrid
        
        if not question:
            return jsonify({'error': 'question is required'}), 400
        
        logger.info(f"Searching in collection {collection_name} for: {question}")
        
        # Get embeddings and client
        embeddings = get_embeddings()
        client = get_opensearch_client()
        index_name = _generate_index_name(collection_name)
        
        if not client.indices.exists(index=index_name):
            return jsonify({'error': f'Collection {collection_name} does not exist'}), 404
        
        # Generate query embedding
        query_vector = embeddings.embed_query(question)
        
        # Build search query based on mode
        if mode == "dense":
            search_body = {
                "size": k,
                "_source": ["chunk_id", "text", "metadata"],
                "query": {
                    "knn": {
                        "embedding": {
                            "vector": query_vector,
                            "k": k
                        }
                    }
                }
            }
        elif mode == "sparse":
            search_body = {
                "size": k,
                "_source": ["chunk_id", "text", "metadata"],
                "query": {
                    "match": {"text": question}
                }
            }
        else:  # hybrid
            search_body = {
                "size": k,
                "_source": ["chunk_id", "text", "metadata"],
                "query": {
                    "hybrid": {
                        "queries": [
                            {
                                "knn": {
                                    "embedding": {
                                        "vector": query_vector,
                                        "k": k * 3
                                    }
                                }
                            },
                            {
                                "match": {"text": question}
                            }
                        ]
                    }
                }
            }
        
        # Execute search
        params = {"search_pipeline": "hybrid_pipeline"} if mode == "hybrid" else {}
        response = client.search(index=index_name, body=search_body, params=params)
        
        logger.info(f"Found {len(response['hits']['hits'])} results")
        
        # Format results
        formatted_results = []
        for hit in response["hits"]["hits"]:
            source = hit["_source"]
            result = {
                'content': source.get("text"),
                'metadata': source.get("metadata", {}),
                'score': float(hit["_score"])
            }
            formatted_results.append(result)
        
        return jsonify({
            'success': True,
            'results': formatted_results,
            'count': len(formatted_results)
        })
        
    except Exception as e:
        logger.error(f"Error searching: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# SCRAPED CONTENT INGESTION ENDPOINT
# ============================================================================

@app.route('/ingest-scraped-content', methods=['POST'])
def ingest_scraped_content():
    """
    Ingest scraped content from Windows scraper
    Accepts JSON with sections and creates embeddings for RAG
    Each server gets its own collection: power_e1180, power_e1150, etc.
    """
    try:
        data = request.get_json()
        
        if not data or not data.get('success'):
            return jsonify({'error': 'Invalid scraped data'}), 400
        
        url = data.get('url', 'unknown')
        page_title = data.get('page_title', 'Untitled')
        sections = data.get('sections', [])
        full_text = data.get('full_text', '')
        server_model = data.get('server_model', None)  # e.g., "E1180"
        
        if not sections:
            return jsonify({'error': 'No sections found in scraped data'}), 400
        
        logger.info(f"Ingesting scraped content from: {url}")
        logger.info(f"Title: {page_title}, Sections: {len(sections)}")
        
        # Create collection name based on server model
        if server_model:
            # Convert E1180 -> power_e1180
            collection_name = f"{OPENSEARCH_DB_PREFIX}_power_{server_model.lower().replace('-', '_')}"
            logger.info(f"Using server-specific collection: {collection_name}")
        else:
            # Fallback to generic collection
            collection_name = f"{OPENSEARCH_DB_PREFIX}_ibm_docs"
            logger.warning(f"No server_model provided, using generic collection: {collection_name}")
        
        # Initialize OpenSearch and embeddings
        client = get_opensearch_client()
        embeddings = get_embeddings()
        
        # Generate index name and create if needed
        index_name = _generate_index_name(collection_name)
        _setup_index(index_name, embeddings.client.get_sentence_embedding_dimension())
        
        # Process sections into documents
        documents = []
        for i, section in enumerate(sections):
            section_title = section.get('title', f'Section {i+1}')
            section_content = section.get('content', [])
            
            # Combine section content
            if isinstance(section_content, list):
                text = '\n'.join([
                    item.get('text', item) if isinstance(item, dict) else str(item)
                    for item in section_content
                ])
            else:
                text = str(section_content)
            
            # Skip empty sections
            if not text.strip():
                continue
            
            # Create document with metadata
            doc = {
                'text': f"{section_title}\n\n{text}",
                'metadata': {
                    'source': url,
                    'page_title': page_title,
                    'section_title': section_title,
                    'section_level': section.get('level', 'unknown'),
                    'section_index': i,
                    'scraped_at': data.get('scraped_at', datetime.now().isoformat()),
                    'scraper_method': data.get('method', 'unknown')
                }
            }
            documents.append(doc)
        
        if not documents:
            return jsonify({'error': 'No valid content found in sections'}), 400
        
        logger.info(f"Processing {len(documents)} documents for indexing")
        
        # Create embeddings and index documents
        indexed_count = 0
        failed_count = 0
        
        for doc in documents:
            try:
                # Generate embedding
                embedding = embeddings.embed_query(doc['text'])
                
                # Create document ID
                doc_id = hashlib.md5(
                    f"{doc['metadata']['source']}_{doc['metadata']['section_index']}".encode()
                ).hexdigest()
                
                # Index document
                client.index(
                    index=index_name,
                    id=doc_id,
                    body={
                        'text': doc['text'],
                        'embedding': embedding,
                        'metadata': doc['metadata']
                    }
                )
                indexed_count += 1
                
            except Exception as e:
                logger.error(f"Failed to index document: {e}")
                failed_count += 1
        
        # Refresh index
        client.indices.refresh(index=index_name)
        
        logger.info(f"Ingestion complete: {indexed_count} indexed, {failed_count} failed")
        
        return jsonify({
            'success': True,
            'collection': collection_name,
            'indexed': indexed_count,
            'failed': failed_count,
            'total_sections': len(sections),
            'page_title': page_title,
            'source_url': url
        })
        
    except Exception as e:
        logger.error(f"Error ingesting scraped content: {e}")
        return jsonify({'error': str(e)}), 500


# ============================================================================
# LLM GENERATION ENDPOINT
# ============================================================================

@app.route('/api/generate', methods=['POST'])
def generate():
    """Generate response from LLM with model selection support"""
    try:
        data = request.get_json()
        prompt = data.get('prompt')
        temperature = data.get('temperature', 0.1)
        n_predict = data.get('n_predict', 100)
        stream = data.get('stream', False)
        model = data.get('model', 'granite')  # 'granite' or 'tinyllama'
        
        if not prompt:
            return jsonify({'error': 'prompt is required'}), 400
        
        # Select LLM service based on model parameter
        if model.lower() == 'tinyllama':
            llm_host = TINYLLAMA_HOST
            llm_port = TINYLLAMA_PORT
            logger.info(f"Using TinyLlama model at {llm_host}:{llm_port}")
        else:
            llm_host = GRANITE_HOST
            llm_port = GRANITE_PORT
            logger.info(f"Using Granite model at {llm_host}:{llm_port}")
        
        logger.info(f"Generating response with temperature={temperature}, n_predict={n_predict}, model={model}, stream={stream}")
        
        # Call LLM service
        llm_url = f"http://{llm_host}:{llm_port}/completion"
        
        payload = {
            "prompt": prompt,
            "temperature": temperature,
            "n_predict": n_predict,
            "stream": stream
        }
        
        # Handle streaming response
        if stream:
            def generate_stream():
                try:
                    with requests.post(llm_url, json=payload, stream=True, timeout=300) as response:
                        response.raise_for_status()
                        for line in response.iter_lines():
                            if line:
                                decoded_line = line.decode('utf-8')
                                if decoded_line.startswith('data: '):
                                    yield f"{decoded_line}\n\n"
                except Exception as e:
                    logger.error(f"Streaming error: {e}")
                    yield f"data: {json.dumps({'error': str(e)})}\n\n"
            
            return Response(generate_stream(), mimetype='text/event-stream')
        
        # Non-streaming response
        response = requests.post(llm_url, json=payload, timeout=180)
        response.raise_for_status()
        
        result = response.json()
        
        return jsonify({
            'success': True,
            'content': result.get('content', ''),
            'model': model,
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
# SALES MANUAL BULK INGESTION ENDPOINTS
# ============================================================================

# Global state for tracking bulk ingestion progress
bulk_ingestion_state = {
    'in_progress': False,
    'current_server': None,
    'completed': [],
    'failed': [],
    'total': 0,
    'started_at': None
}

@app.route('/api/ingest-sales-manual', methods=['POST'])
def ingest_sales_manual():
    """
    Trigger scraping and ingestion of a single IBM Power server Sales Manual
    Calls the Windows scraper service and ingests the results
    """
    try:
        data = request.get_json()
        server_model = data.get('server_model')
        server_name = data.get('server_name')
        processor = data.get('processor', 'POWER')
        
        if not server_model:
            return jsonify({'error': 'server_model is required'}), 400
        
        logger.info(f"Starting Sales Manual ingestion for {server_model} ({server_name})")
        
        # Update bulk ingestion state
        bulk_ingestion_state['current_server'] = server_model
        
        # Call Windows scraper service
        # The scraper is running on the Windows laptop
        scraper_url = os.environ.get('SCRAPER_URL', 'http://host.docker.internal:5000')
        
        logger.info(f"Calling scraper at {scraper_url}/scrape")
        
        try:
            scraper_response = requests.post(
                f"{scraper_url}/scrape",
                json={'server_model': server_model},
                timeout=600  # 10 minute timeout for scraping
            )
            scraper_response.raise_for_status()
            scraper_data = scraper_response.json()
            
            if not scraper_data.get('success'):
                error_msg = scraper_data.get('error', 'Scraping failed')
                logger.error(f"Scraper failed for {server_model}: {error_msg}")
                bulk_ingestion_state['failed'].append({
                    'server': server_model,
                    'error': error_msg
                })
                return jsonify({'error': error_msg}), 500
            
            logger.info(f"Scraping successful for {server_model}, got {scraper_data.get('sections_count', 0)} sections")
            
        except requests.exceptions.Timeout:
            error_msg = f"Scraper timeout for {server_model}"
            logger.error(error_msg)
            bulk_ingestion_state['failed'].append({
                'server': server_model,
                'error': 'Timeout'
            })
            return jsonify({'error': error_msg}), 504
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Failed to call scraper: {str(e)}"
            logger.error(error_msg)
            bulk_ingestion_state['failed'].append({
                'server': server_model,
                'error': str(e)
            })
            return jsonify({'error': error_msg}), 500
        
        # Now ingest the scraped content
        # Collection name: power_e1180, power_e1050, etc.
        collection_name = f"power_{server_model.lower().replace('-', '_')}"
        
        logger.info(f"Ingesting scraped content into collection: {collection_name}")
        
        # Call the existing ingest-scraped-content endpoint
        ingest_response = requests.post(
            'http://localhost:8080/ingest-scraped-content',
            json={
                'collection_name': collection_name,
                'scraped_data': scraper_data
            },
            timeout=300  # 5 minute timeout for ingestion
        )
        
        if ingest_response.status_code == 200:
            ingest_data = ingest_response.json()
            logger.info(f"Successfully ingested {server_model}: {ingest_data.get('indexed', 0)} documents")
            bulk_ingestion_state['completed'].append(server_model)
            
            return jsonify({
                'success': True,
                'server_model': server_model,
                'collection': collection_name,
                'indexed': ingest_data.get('indexed', 0),
                'sections': scraper_data.get('sections_count', 0)
            })
        else:
            error_msg = f"Ingestion failed: {ingest_response.text}"
            logger.error(error_msg)
            bulk_ingestion_state['failed'].append({
                'server': server_model,
                'error': 'Ingestion failed'
            })
            return jsonify({'error': error_msg}), 500
            
    except Exception as e:
        logger.error(f"Error in ingest_sales_manual: {e}")
        bulk_ingestion_state['failed'].append({
            'server': server_model if 'server_model' in locals() else 'unknown',
            'error': str(e)
        })
        return jsonify({'error': str(e)}), 500
    finally:
        bulk_ingestion_state['current_server'] = None
        
        # Check if bulk ingestion is complete
        if bulk_ingestion_state['in_progress']:
            total_processed = len(bulk_ingestion_state['completed']) + len(bulk_ingestion_state['failed'])
            if total_processed >= bulk_ingestion_state['total']:
                bulk_ingestion_state['in_progress'] = False
                logger.info(f"Bulk ingestion complete: {len(bulk_ingestion_state['completed'])} succeeded, {len(bulk_ingestion_state['failed'])} failed")


@app.route('/api/bulk-ingestion-status', methods=['GET'])
def bulk_ingestion_status():
    """
    Get the current status of bulk ingestion process
    Returns progress information for polling
    """
    try:
        return jsonify({
            'in_progress': bulk_ingestion_state['in_progress'],
            'current_server': bulk_ingestion_state['current_server'],
            'completed': bulk_ingestion_state['completed'],
            'failed': bulk_ingestion_state['failed'],
            'total': bulk_ingestion_state['total'],
            'completed_count': len(bulk_ingestion_state['completed']),
            'failed_count': len(bulk_ingestion_state['failed']),
            'started_at': bulk_ingestion_state['started_at']
        })
    except Exception as e:
        logger.error(f"Error getting bulk ingestion status: {e}")
        return jsonify({'error': str(e)}), 500
@app.route('/api/init-bulk-ingestion', methods=['POST'])
def init_bulk_ingestion():
    """
    Initialize the bulk ingestion state before starting
    Called by frontend before triggering individual server ingestions
    """
    try:
        data = request.get_json()
        total = data.get('total', 0)
        
        # Reset the bulk ingestion state
        bulk_ingestion_state['in_progress'] = True
        bulk_ingestion_state['current_server'] = None
        bulk_ingestion_state['completed'] = []
        bulk_ingestion_state['failed'] = []
        bulk_ingestion_state['total'] = total
        bulk_ingestion_state['started_at'] = datetime.now().isoformat()
        
        logger.info(f"Initialized bulk ingestion for {total} servers")
        
        return jsonify({
            'success': True,
            'message': f'Bulk ingestion initialized for {total} servers'
        })
    except Exception as e:
        logger.error(f"Error initializing bulk ingestion: {e}")
        return jsonify({'error': str(e)}), 500




# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    try:
        # Check OpenSearch
        client = get_opensearch_client()
        client.cluster.health()
        opensearch_status = "connected"
    except Exception as e:
        logger.error(f"OpenSearch health check failed: {e}")
        opensearch_status = "disconnected"
    
    # Check LLM service
    try:
        llm_url = f"http://{LLAMA_HOST}:{LLAMA_PORT}/health"
        response = requests.get(llm_url, timeout=5)
        llm_status = "connected" if response.status_code == 200 else "disconnected"
    except:
        llm_status = "disconnected"
    
    overall_status = "healthy" if opensearch_status == "connected" else "degraded"
    
    return jsonify({
        'status': overall_status,
        'opensearch': opensearch_status,
        'llm': llm_status
    }), 200 if overall_status == "healthy" else 503

# ============================================================================
# ROOT ENDPOINT
# ============================================================================

@app.route('/', methods=['GET'])
def root():
    """API documentation"""
    return jsonify({
        'service': 'RAG Backend with OpenSearch',
        'version': '3.1.0',
        'endpoints': {
            'collections': {
                'GET /api/collections': 'List all collections',
                'DELETE /api/collections/<name>': 'Drop a collection'
            },
            'documents': {
                'POST /api/load-pdf': 'Load PDF into vector database',
                'POST /ingest-scraped-content': 'Ingest scraped content from Windows scraper',
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
    # Create PDF directory if it doesn't exist
    os.makedirs(PDF_DIR, exist_ok=True)
    
    logger.info(f"OpenSearch host: {OPENSEARCH_HOST}:{OPENSEARCH_PORT}")
    logger.info(f"PDF directory: {PDF_DIR}")
    logger.info(f"Docling enabled: {USE_DOCLING}")
    logger.info(f"Docling config: {docling_config_dict()}")
    logger.info("Starting RAG Backend with OpenSearch...")
    
    app.run(host='0.0.0.0', port=8080, debug=False)

# Made with Bob
