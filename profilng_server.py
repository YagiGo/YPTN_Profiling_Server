from flask import Flask, render_template,request
from WProfX import main as fetch
from WProfX import trace_parser as profiler


app = Flask(__name__)


@app.route('/')
def hello_world():
    return render_template('index.html', name='joe')
@app.route('/receiver', methods=['POST'])
def worker():
    #print(request.get_data())
    # Insert Profiling part here
    requested_site = request.get_data().decode('utf-8')
    fetch.traceWithInput(requested_site)
    profiler.analyzeTrace(requested_site.split('/')[-1])
    return request.get_data()


if __name__ == '__main__':
    app.run("0.0.0.0", 5000)
