from flask import Flask, render_template,request, jsonify,send_from_directory
from flask import g
import os, json
from WProfX import main as fetch
from WProfX import trace_parser as profiler
app = Flask(__name__)
@app.before_request
def before_request():
    g.site = ''
@app.route('/')
def initPage():
    return render_template('index.html', name='index')
@app.route('/receiver', methods=['POST'])
def work():
    #print(request.get_data())
    # Insert Profiling part here
    requested_site = request.get_data().decode('utf-8')
    setattr(g, 'site', requested_site)
    print("g is " + g.site)
    fetch.traceWithInput(requested_site)
    profiler.analyzeTrace(requested_site.split('/')[-1])
    response = {'status':200, 'site':requested_site}
    # response = make_response('Analysis Finished', 200)
    return jsonify(response)
@app.route('/profiled_result', methods=['POST', 'GET'])
def showProfiledResult():
    requested_site = request.get_data().decode('utf-8')
    g.site = requested_site
    print(g.site)
    template_name = '/profiled_result/' + 'www.facebook.com' + '.html'
    print("Template Name is " + template_name)
    return render_template(template_name)

@app.route('/profiled_data', methods=['POST'])
def showProfiledData():
    requested_site = request.get_data().decode('utf-8')
    jsonFilePath = ''.join([os.path.normpath(os.path.dirname(os.path.realpath(__file__))), '/WProfX', '/graphs/',
                        '0_', requested_site.split('/')[-1].replace(" ", ""), '.json'])
    print(jsonFilePath)
    with open(jsonFilePath, 'r') as f:
        return f.read()
if __name__ == '__main__':
    app.run("0.0.0.0", 5000)

