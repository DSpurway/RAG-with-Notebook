from pymilvus import connections, utility
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Milvus
from langchain.document_loaders import WebBaseLoader, PyPDFLoader
from langchain.text_splitter import CharacterTextSplitter
from flask import Flask, request
from flask_cors import CORS, cross_origin
import os
import logging

app = Flask(__name__)
CORS(app, origins=["https://rag-webpage-llm-on-techzone.apps.p1370.cecc.ihost.com"]) 

if __name__ != '__main__':
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)

@app.route('/')
@cross_origin() # allow all origins all methods.
def index():
    content = {}

    if request.args.get('Server_Name'):
        Server_Name = request.args.get('Server_Name')
        app.logger.info('Found Server_Name '+Server_Name)
        
        MILVUS_HOST="milvus-service"
        MILVUS_PORT="19530"

        connections.connect(host=MILVUS_HOST, port=MILVUS_PORT)
        app.logger.info('Connected to Milvus Host '+MILVUS_HOST)
        
        FNAME = Server_Name+".pdf"
        
        loader = PyPDFLoader(FNAME)
        app.logger.info('Loading file '+FNAME)
        
        docs = loader.load()
        
        text_splitter = CharacterTextSplitter(separator="\n", chunk_size=768, chunk_overlap=0)
        docs = text_splitter.split_documents(docs)
        app.logger.info('Splitting Text')
        app.logger.info('Text split into '+str(len(docs))+' chunks')
        
        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        app.logger.info('Getting embeddings')

        app.logger.info('Beginning vector store')
        vector_store = Milvus.from_documents(
            docs,
            embedding=embeddings,
            collection_name="sales_manuals",
            connection_args={"host": MILVUS_HOST, "port": MILVUS_PORT}
        )
        app.logger.info('Completed vector store')
        
        content['result'] = "Success"
    else:
        content ['result'] = "Server Name Missing"
        
    return content

@app.route('/healthz')
# Added healthcheck endpoint
def healthz():
    return "ok"

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
