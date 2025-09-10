# FROM registry.access.redhat.com/ubi9 AS builder
FROM registry.access.redhat.com/ubi9

RUN dnf -y install gcc-toolset-13 && \
    source /opt/rh/gcc-toolset-13/enable

# install build tools and clone and compile llama.cpp
RUN dnf -y update && dnf install -y git make cmake automake gcc gcc-c++ llvm-toolset wget
    
RUN wget --quiet https://repo.anaconda.com/archive/Anaconda3-2023.09-0-Linux-ppc64le.sh -O ~/conda.sh && \
    /bin/bash ~/conda.sh -b -p /opt/conda

# Put conda in path so we can use conda activate
ENV PATH /opt/conda/bin:$PATH

RUN conda update -n base -c defaults conda && \
    conda config --prepend channels rocketce && \
    conda config --append channels conda-forge && \
    conda install -y pytorch-cpu -c rocketce && \
    conda install -y gfortran -c conda-forge && \
    conda install -y openblas -c rocketce && \
    conda install -y llama.cpp -c rocketce

RUN mkdir -p /models
    
# RUN wget --quiet https://huggingface.co/bartowski/granite-3.0-8b-instruct-GGUF/resolve/main/granite-3.0-8b-instruct-Q4_K_M.gguf -O /models/granite-3.0-8b-instruct-Q4_K_M.gguf
#   wget --quiet https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q8_0.gguf -O /models/tinyllama-1.1b-chat-v1.0.Q8_0.gguf
#   wget --quiet https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF/resolve/main/llama-2-7b-chat.Q8_0.gguf -O /models/llama-2-7b-chat.Q8_0.gguf
RUN wget --quiet https://huggingface.co/TheBloke/deepseek-llm-7B-chat-GGUF/resolve/main/deepseek-llm-7b-chat.Q8_0.gguf -O /models/deepseek-llm-7b-chat.Q8_0.gguf

ENTRYPOINT ["llama-server", "-m", "/models/deepseek-llm-7b-chat.Q8_0.gguf", "--prio", "3", "-c", "4096","-b", "32", "-t", "40", "-n", "-1", "--mlock", "--host", "0.0.0.0"]
