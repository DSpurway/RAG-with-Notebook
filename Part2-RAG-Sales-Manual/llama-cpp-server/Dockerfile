#FROM registry.access.redhat.com/ubi9/ubi as builder
FROM registry.access.redhat.com/ubi9/ubi

RUN dnf -y update && dnf install -y git automake gcc gcc-c++ llvm-toolset ninja-build python3.12 python3.12-pip python3.12-devel gfortran curl-devel wget
RUN python3.12 -m venv venv
ENV PATH="./.venv/bin:$PATH"
RUN pip install --prefer-binary make cmake torch openblas --extra-index-url=https://wheels.developerfirst.ibm.com/ppc64le/linux
ENV LD_LIBRARY_PATH=./.venv/lib/python3.12/site-packages/openblas/lib:$LD_LIBRARY_PATH

#RUN git clone --recursive https://github.com/OpenMathLib/OpenBLAS.git
#WORKDIR OpenBLAS
#RUN git checkout v0.3.30
#RUN make -j16 TARGET=POWER10 BINARY=64 USE_OPENMP=1 USE_THREAD=1 NUM_THREADS=120 DYNAMIC_ARCH=1 INTERFACE64=0
#RUN make install
#WORKDIR /

#ENV BLAS_LIBRARIES=/opt/OpenBLAS/lib/libopenblas.so
#ENV BLAS_INCLUDE_DIRS=/opt/OpenBLAS/include

RUN git clone https://github.com/ggml-org/llama.cpp.git
WORKDIR llama.cpp
RUN git checkout b6122
RUN LD_LIBRARY_PATH=/opt/lib cmake -B build \
    -DGGML_BLAS=ON \
    -DGGML_BLAS_VENDOR=OpenBLAS \
    -DBLAS_LIBRARIES=/opt/OpenBLAS/lib/libopenblas.so \
    -DBLAS_INCLUDE_DIRS=/opt/OpenBLAS/include \
    -DGGML_CUDA=OFF

RUN cmake --build build --config Release 

EXPOSE 8080

RUN mkdir -p /models
RUN wget --quiet https://huggingface.co/ibm-granite/granite-3.3-2b-instruct-GGUF/resolve/main/granite-3.3-2b-instruct-Q4_K_M.gguf -O /models/granite-3.3-2b-instruct-Q4_K_M.gguf
    
#RUN wget --quiet https://huggingface.co/bartowski/granite-3.0-8b-instruct-GGUF/resolve/main/granite-3.0-8b-instruct-Q4_K_M.gguf -O /models/granite-3.0-8b-instruct-Q4_K_M.gguf
#RUN wget --quiet https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q8_0.gguf -O /models/tinyllama-1.1b-chat-v1.0.Q8_0.gguf
#RUN wget --quiet https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF/resolve/main/llama-2-7b-chat.Q8_0.gguf -O /models/llama-2-7b-chat.Q8_0.gguf
#RUN wget --quiet https://huggingface.co/TheBloke/deepseek-llm-7B-chat-GGUF/resolve/main/deepseek-llm-7b-chat.Q8_0.gguf -O /models/deepseek-llm-7b-chat.Q8_0.gguf

#ENTRYPOINT ["llama-server", "-m", "/models/deepseek-llm-7b-chat.Q8_0.gguf", "--prio", "3", "-c", "4096","-b", "32", "-t", "40", "-n", "-1", "--mlock", "--host", "0.0.0.0"]
ENTRYPOINT [ "/llama.cpp/build/bin/llama-server", "-m", "/models/granite-3.3-2b-instruct-Q4_K_M.gguf", "--host", "0.0.0.0"]
