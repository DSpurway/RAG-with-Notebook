from pymilvus import connections, utility
from flask import Flask, request
import os
import logging

app = Flask(__name__)

if __name__ != '__main__':
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)

@app.route('/')
def index():
    content = {}

    if request.args.get('Collection'):
        Collection = request.args.get('Collection')
        app.logger.info('Found Server_Name '+Collection)
        
        MILVUS_HOST="milvus-service"
        MILVUS_PORT="19530"

        connections.connect(host=MILVUS_HOST, port=MILVUS_PORT)
        app.logger.info('Connected to Milvus Host '+MILVUS_HOST)

        app.logger.info('Dropping collection'+Collection)
        utility.drop_collection(Collection)
        app.logger.info('Dropped collection'+Collection)
        
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