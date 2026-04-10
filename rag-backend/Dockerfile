# Multi-stage build for RAG Backend Service
FROM registry.access.redhat.com/ubi9/python-312:latest AS builder

USER root

# Install system dependencies required for building Python packages
RUN dnf install -y \
    gcc \
    gcc-c++ \
    git \
    make \
    cmake \
    automake \
    llvm-toolset \
    ninja-build \
    gfortran \
    curl-devel \
    wget \
    python3.12-devel \
    && dnf clean all

# Create app directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
# Ensure setuptools/pkg_resources is present for source builds, then install torch/openblas
# from IBM Power wheels first, then install the remaining requirements
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir --prefer-binary torch openblas --extra-index-url=https://wheels.developerfirst.ibm.com/ppc64le/linux && \
    grep -v "^torch==" requirements.txt > requirements-no-torch.txt && \
    pip install --no-cache-dir -r requirements-no-torch.txt

# Copy application code
COPY app.py .

# Create PDF directory
RUN mkdir -p /app/pdfs

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
COPY --from=builder /app/pdfs /app/pdfs

# Environment variables with defaults
ENV MILVUS_HOST=milvus-service \
    MILVUS_PORT=19530 \
    LLAMA_HOST=llama-service \
    LLAMA_PORT=8080 \
    PDF_DIR=/app/pdfs \
    CORS_ORIGIN=* \
    PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/health', timeout=5)"

# Run with gunicorn for production
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "--threads", "4", "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-", "app:app"]