## Assisted by WCA@IBM
## Latest GenAI contribution: ibm/granite-20b-code-instruct-v2from flask import Flask, render_template
from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def index():
    return render_template('index.html')
  
@app.route('/healthz')
# Added healthcheck endpoint
def healthz():
    return "ok"

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
