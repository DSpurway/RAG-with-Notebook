# Multi-stage build for RAG Backend Service with OpenSearch
# Simplified - no Rust compiler or custom SQLite needed!
FROM registry.access.redhat.com/ubi9/python-312:latest AS builder

USER root

# Install system dependencies required for building Python packages
RUN dnf install -y \
    gcc \
    gcc-c++ \
    git \
    make \
    python3.12-devel \
    openblas-devel \
    lcms2-devel \
    freetype \
    libjpeg-turbo \
    && dnf clean all

# Create app directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
# Use IBM Power-optimized wheels where available for better performance
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir --prefer-binary \
        torch==2.9.1 \
        torchvision==0.24.1 \
        sentence-transformers \
        transformers \
        lxml \
        numpy \
        --extra-index-url=https://wheels.developerfirst.ibm.com/ppc64le/linux && \
    grep -Ev "^(torch|torchvision|sentence-transformers|transformers|huggingface-hub|tokenizers|lxml|numpy)" requirements.txt > requirements-base.txt && \
    pip install --no-cache-dir --prefer-binary -r requirements-base.txt \
        --extra-index-url=https://wheels.developerfirst.ibm.com/ppc64le/linux && \
    mkdir -p /app/docling-models

# Copy application code
COPY app.py .
COPY web_scraper.py .
COPY docling_config.py .
COPY token_utils.py .
COPY docling_converter.py .
COPY hierarchical_chunker.py .

# Create PDF directory and copy sample PDFs
RUN mkdir -p /app/pdfs
COPY pdfs/*.pdf /app/pdfs/

# ============================================================================
# Production Stage
# ============================================================================
FROM registry.access.redhat.com/ubi9/python-312:latest

USER root

# Install only runtime dependencies
RUN dnf install -y \
    libgomp \
    && dnf clean all

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /opt/app-root/lib/python3.12/site-packages /opt/app-root/lib/python3.12/site-packages
COPY --from=builder /opt/app-root/bin /opt/app-root/bin

# Copy application
COPY --from=builder /app/app.py .
COPY --from=builder /app/web_scraper.py .
COPY --from=builder /app/docling_config.py .
COPY --from=builder /app/token_utils.py .
COPY --from=builder /app/docling_converter.py .
COPY --from=builder /app/hierarchical_chunker.py .
COPY --from=builder /app/pdfs /app/pdfs

# Environment variables with defaults
ENV OPENSEARCH_HOST=opensearch-service \
    OPENSEARCH_PORT=9200 \
    OPENSEARCH_USERNAME=admin \
    OPENSEARCH_PASSWORD=admin \
    OPENSEARCH_DB_PREFIX=rag \
    OPENSEARCH_INDEX_NAME=default \
    OPENSEARCH_NUM_SHARDS=1 \
    LLAMA_HOST=llama-service \
    LLAMA_PORT=8080 \
    PDF_DIR=/app/pdfs \
    DOCLING_MODELS_PATH=/app/docling-models \
    USE_DOCLING=false \
    ENABLE_TABLES=true \
    ENABLE_OCR=false \
    DOCLING_CHUNK_SIZE=768 \
    DOCLING_CHUNK_OVERLAP=50 \
    PDF_CHUNK_SIZE=100 \
    CORS_ORIGIN=* \
    PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/health', timeout=5)"

# Run with gunicorn for production
# Timeout set to 1200s (20 minutes) to allow for Docling PDF processing
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "--threads", "4", "--timeout", "1200", "--access-logfile", "-", "--error-logfile", "-", "app:app"]