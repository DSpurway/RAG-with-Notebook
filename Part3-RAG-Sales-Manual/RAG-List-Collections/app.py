from pymilvus import connections, utility
from flask import Flask
from flask_cors import CORS, cross_origin
import logging

app = Flask(__name__)
CORS(app, origins=["https://rag-webpage-llm-on-techzone.apps.p1293.cecc.ihost.com"]) 

app = Flask(__name__)

if __name__ != '__main__':
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)

@app.route('/')
@cross_origin() # allow all origins all methods.
def index():
    content = {}
        
    MILVUS_HOST="milvus-service"
    MILVUS_PORT="19530"
        
    connections.connect(host=MILVUS_HOST, port=MILVUS_PORT)
    app.logger.info('Connected to Milvus Host '+MILVUS_HOST)
        
    Collections = utility.list_collections()
    app.logger.info('Found collections:', Collections)
        
    content['result'] = Collections  
    
    return content
    
@app.route('/healthz')
# Added healthcheck endpoint
def healthz():
    return "ok"

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
