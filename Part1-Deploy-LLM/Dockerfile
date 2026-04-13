FROM registry.access.redhat.com/ubi9/ubi

# Install build dependencies
RUN dnf -y update && dnf install -y \
    git \
    make \
    cmake \
    automake \
    gcc \
    gcc-c++ \
    llvm-toolset \
    ninja-build \
    python3.12 \
    python3.12-pip \
    python3.12-devel \
    gfortran \
    curl-devel \
    wget \
    && dnf clean all

# Create and activate Python virtual environment
RUN python3.12 -m venv .venv
RUN source .venv/bin/activate && \
    pip install --prefer-binary torch openblas --extra-index-url=https://wheels.developerfirst.ibm.com/ppc64le/linux

# Set up environment
ENV PATH="/.venv/bin:$PATH"
ENV LD_LIBRARY_PATH=/.venv/lib/python3.12/site-packages/openblas/lib:$LD_LIBRARY_PATH

# Clone and build llama.cpp
RUN git clone https://github.com/ggml-org/llama.cpp.git
WORKDIR /llama.cpp
RUN git checkout b6122
RUN LD_LIBRARY_PATH=/opt/lib cmake -B build \
    -DGGML_BLAS=ON \
    -DGGML_BLAS_VENDOR=OpenBLAS \
    -DBLAS_LIBRARIES=/.venv/lib/python3.12/site-packages/openblas/lib/libopenblas.so \
    -DBLAS_INCLUDE_DIRS=/.venv/lib/python3.12/site-packages/openblas/include \
    -DGGML_CUDA=OFF

RUN cmake --build build --config Release 

# Create models directory
RUN mkdir -p /models

# Download BOTH models
# TinyLlama for Part 1 (basic demonstrations)
RUN wget --quiet \
    https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q8_0.gguf \
    -O /models/tinyllama-1.1b-chat-v1.0.Q8_0.gguf

# Granite 4.0 Micro for Part 2/3 (RAG with complex documents)
RUN wget --quiet \
    https://huggingface.co/ibm-granite/granite-4.0-micro-GGUF/resolve/main/granite-4.0-micro-Q4_K_M.gguf \
    -O /models/granite-4.0-micro-Q4_K_M.gguf

# Create startup script that allows model selection
RUN cat > /start-llama.sh << 'EOF'
#!/bin/bash

# Default to TinyLlama for Part 1
MODEL_NAME=${LLM_MODEL:-tinyllama}

case "$MODEL_NAME" in
  tinyllama)
    MODEL_PATH="/models/tinyllama-1.1b-chat-v1.0.Q8_0.gguf"
    echo "Starting with TinyLlama (Part 1 - Basic demonstrations)"
    ;;
  granite)
    MODEL_PATH="/models/granite-4.0-micro-Q4_K_M.gguf"
    echo "Starting with Granite 4.0 Micro (Part 2/3 - RAG with complex documents)"
    ;;
  *)
    echo "Unknown model: $MODEL_NAME"
    echo "Valid options: tinyllama, granite"
    echo "Defaulting to TinyLlama"
    MODEL_PATH="/models/tinyllama-1.1b-chat-v1.0.Q8_0.gguf"
    ;;
esac

echo "Model path: $MODEL_PATH"
echo "Starting llama-server..."

# Start llama-server with the selected model
exec /llama.cpp/build/bin/llama-server \
    -m "$MODEL_PATH" \
    --host 0.0.0.0 \
    --port 8080 \
    -c 4096 \
    -t 16
EOF

RUN chmod +x /start-llama.sh

EXPOSE 8080

# Use the startup script as entrypoint
ENTRYPOINT ["/start-llama.sh"]