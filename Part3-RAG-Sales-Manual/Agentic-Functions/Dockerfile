FROM registry.access.redhat.com/ubi8/python-311

# Upgrade pip and install Python dependencies
RUN pip3 install --upgrade pip
RUN pip3 install torch torchvision transformers llama-cpp-python --extra-index-url https://repo.fury.io/mgiessing --prefer-binary
RUN pip3 install -U langchain
RUN pip3 install -U langchain-community
RUN pip3 install -U python-dotenv
RUN pip3 install -U jupyter

RUN mkdir -p /tmp/notebooks && chmod -R a+rwx /tmp/notebooks
WORKDIR /tmp/notebooks

CMD ["jupyter", "notebook", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--allow-root", "--notebook-dir=/tmp/notebooks", "--NotebookApp.token=''", "--NotebookApp.allow_origin='*'"]
