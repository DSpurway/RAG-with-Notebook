FROM registry.access.redhat.com/ubi9/ubi

#RUN dnf -y update && dnf install -y git make cmake automake gcc gcc-c++ llvm-toolset ninja-build python3.12 python3.12-pip python3.12-devel gfortran 
RUN dnf -y update && dnf install -y python3.12 python3.12-pip python3.12-devel nodejs

RUN python3.12 -m venv .venv
#RUN source .venv/bin/activate && pip install --prefer-binary llama-cpp-python==0.3.14 torch openblas pymilvus sentence-transformers langchain langchain-community langchain-huggingface jupyter --extra-index-url=https://wheels.developerfirst.ibm.com/ppc64le/linux
RUN source .venv/bin/activate && pip install --upgrade pip
RUN source .venv/bin/activate && pip install --prefer-binary notebook --extra-index-url=https://wheels.developerfirst.ibm.com/ppc64le/linux

ENV PATH="/.venv/bin:$PATH"
#ENV LD_LIBRARY_PATH=/.venv/lib/python3.12/site-packages/openblas/lib:/.venv/lib/python3.12/site-packages/libprotobuf/lib64:$LD_LIBRARY_PATH

RUN mkdir -p /.local && chmod -R a+rwx /.local
RUN mkdir -p /.venv/notebooks && chmod -R a+rwx /.venv/notebooks
WORKDIR /.venv/notebooks
RUN npm update
RUN npm install --save jupyter-js-notebook

CMD ["jupyter", "notebook", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--allow-root", "--notebook-dir=/.venv/notebooks", "--NotebookApp.token=''", "--NotebookApp.allow_origin='*'"]
