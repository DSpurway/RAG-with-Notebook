from pymilvus import connections, utility
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Milvus
from langchain_core.load import dumps
from flask import Flask, request
from flask_cors import CORS, cross_origin
import os
import logging

app = Flask(__name__)
CORS(app, origins=["https://rag-webpage-llm-on-techzone.apps.p1309.cecc.ihost.com"]) 

app = Flask(__name__)

if __name__ != '__main__':
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)

@app.route('/')
@cross_origin() # allow all origins all methods.
def index():
    content = {}

    if request.args.get('Report_Name','Question'):
        Report_Name = request.args.get('Report_Name')
        app.logger.info('Found Report_Name '+Report_Name)

        Question = request.args.get('Question')
        app.logger.info('Found Question '+Question)
        
        MILVUS_HOST="milvus-service"
        MILVUS_PORT="19530"

        connections.connect(host=MILVUS_HOST, port=MILVUS_PORT)
        app.logger.info('Connected to Milvus Host '+MILVUS_HOST)

        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

        vector_store = Milvus(
            embedding_function=embeddings,
            collection_name="annual_reports",
            connection_args={"host": MILVUS_HOST, "port": MILVUS_PORT}
        )

        FNAME = Report_Name+".pdf"

        app.logger.info('Using this question to retrieve docs: '+Question)

        docs = vector_store.similarity_search_with_score(Question, k=3, expr="source == '"+FNAME+"'")
        app.logger.info('Got docs from vector store')
        
        content['result'] = "Success"
        content['docs'] = dumps(docs)
    else:
        content ['result'] = "Report Name or Question Missing"

    app.logger.info('Returning '+str(content))
    return content

@app.route('/healthz')
# Added healthcheck endpoint
def healthz():
    return "ok"

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
