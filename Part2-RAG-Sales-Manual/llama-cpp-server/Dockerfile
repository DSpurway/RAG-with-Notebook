FROM registry.access.redhat.com/ubi9/ubi
ENV BLA_VENDOR=OpenBLAS

RUN dnf -y update && dnf install -y git automake gcc gcc-c++ llvm-toolset ninja-build python3-pip python3-devel
RUN pip install --prefer-binary make cmake wget pytorch --extra-index-url=https://wheels.developerfirst.ibm.com/ppc64le/linux

#    conda install -y pytorch-cpu -c rocketce && \
#    conda install -y gfortran -c conda-forge && \
#    conda install -y openblas -c rocketce && \
#    conda install -y llama.cpp -c rocketce

#RUN mkdir -p /models
    
# RUN wget --quiet https://huggingface.co/bartowski/granite-3.0-8b-instruct-GGUF/resolve/main/granite-3.0-8b-instruct-Q4_K_M.gguf -O /models/granite-3.0-8b-instruct-Q4_K_M.gguf
#   wget --quiet https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q8_0.gguf -O /models/tinyllama-1.1b-chat-v1.0.Q8_0.gguf
#   wget --quiet https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF/resolve/main/llama-2-7b-chat.Q8_0.gguf -O /models/llama-2-7b-chat.Q8_0.gguf
#RUN wget --quiet https://huggingface.co/TheBloke/deepseek-llm-7B-chat-GGUF/resolve/main/deepseek-llm-7b-chat.Q8_0.gguf -O /models/deepseek-llm-7b-chat.Q8_0.gguf

#ENTRYPOINT ["llama-server", "-m", "/models/deepseek-llm-7b-chat.Q8_0.gguf", "--prio", "3", "-c", "4096","-b", "32", "-t", "40", "-n", "-1", "--mlock", "--host", "0.0.0.0"]
