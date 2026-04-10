from flask import Flask, request
from flask_cors import CORS, cross_origin
import logging
import requests

app = Flask(__name__)
CORS(app, origins=["https://rag-webpage-llm-on-techzone.apps.p1293.cecc.ihost.com"]) 

app = Flask(__name__)

if __name__ != '__main__':
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)

@app.route('/', methods=['POST'])
@cross_origin() # allow all origins all methods.
def index():
    content = {}
    
    LLAMA_HOST="llama-service"
    LLAMA_PORT="8080"
    
    if request.method == 'POST':
        data = request.get_json()
        app.logger.info('Received data: ' +str(data))
        Prompt = data
        app.logger.info('Received prompt: ' + Prompt)
        
        json_data = {
            'prompt': Prompt,
            'temperature': 0.1,
            'n_predict': 100,
            'stream': False,
        }
        app.logger.info('Sending request to the LLM with this JSON data: '+str(json_data))
        
        res = requests.post(f'http://{LLAMA_HOST}:{LLAMA_PORT}/completion', json=json_data, timeout=60)
        app.logger.info('Recieved this from the LLM: '+str(res.json()))
        
        answer = res.json()['content']
        content['result'] = "Success"
        content['answer'] = answer
    elif request.args.get('Prompt'):
        Prompt = request.args.get('Prompt')
        app.logger.info('Found Prompt '+Prompt)
        
        json_data = {
            'prompt': Prompt,
            'temperature': 0.1,
            'n_predict': 100,
            'stream': False,
        }
        app.logger.info('Sending request to the LLM with this JSON data: '+str(json_data))
        
        res = requests.post(f'http://{LLAMA_HOST}:{LLAMA_PORT}/completion', json=json_data)
        app.logger.info('Recieved this from the LLM: '+str(res.json()))
        
        answer = res.json()['content']
        content['result'] = "Success"
        content['answer'] = answer
    else:
        content ['result'] = "Prompt Missing"
    
    app.logger.info('Returning '+str(content))
    return content

@app.route('/healthz')
# Added healthcheck endpoint
def healthz():
    return "ok"

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
