## Assisted by WCA@IBM
## Latest GenAI contribution: ibm/granite-20b-code-instruct-v2
from flask import Flask, render_template, jsonify
import os

app = Flask(__name__)

# Get service URLs from environment variables with sensible defaults
def get_service_url(service_name, default_port=8080):
    """Get service URL from environment or construct from OpenShift service name"""
    env_var = f'{service_name.upper().replace("-", "_")}_URL'
    url = os.environ.get(env_var)
    
    if not url:
        # Try to construct from OpenShift internal service name
        namespace = os.environ.get('NAMESPACE', 'llm-on-techzone')
        base_domain = os.environ.get('BASE_DOMAIN', 'apps.cecc.ihost.com')
        url = f'https://{service_name}-{namespace}.{base_domain}'
    
    return url

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/config.js")
def config():
    """Serve dynamic configuration based on environment"""
    config_js = f"""
// Auto-generated configuration
window.RAG_CONFIG = {{
    listCollectionsUrl: '{get_service_url("rag-list-collections")}',
    dropCollectionUrl: '{get_service_url("rag-drop-collection")}',
    loaderUrl: '{get_service_url("rag-loader")}',
    getDocsUrl: '{get_service_url("rag-get-docs")}',
    promptLlmUrl: '{get_service_url("rag-prompt-llm")}'
}};
"""
    return config_js, 200, {'Content-Type': 'application/javascript'}
  
@app.route('/healthz')
def healthz():
    return "ok"

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
