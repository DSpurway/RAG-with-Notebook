FROM registry.access.redhat.com/ubi9/ubi

RUN dnf -y update && dnf install -y  make cmake automake gcc gcc-c++ llvm-toolset ninja-build python3.12 python3.12-pip python3.12-devel
RUN python3.12 -m venv .venv
RUN source .venv/bin/activate && pip install --prefer-binary torch openblas pymilvus sentence-transformers llama-cpp-python langchain langchain-community jupyter --extra-index-url=https://wheels.developerfirst.ibm.com/ppc64le/linux
ENV PATH="/.venv/bin:$PATH"
ENV LD_LIBRARY_PATH=/.venv/lib/python3.12/site-packages/openblas/lib:$LD_LIBRARY_PATH

RUN mkdir -p /.venv/notebooks && chmod -R a+rwx /.venv/notebooks
WORKDIR /.venv/notebooks

CMD ["jupyter", "notebook", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--allow-root", "--notebook-dir=/.venv/notebooks", "--NotebookApp.token=''", "--NotebookApp.allow_origin='*'"]
