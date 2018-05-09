from flask import Flask, render_template,request, make_response, jsonify
from WProfX import main as fetch
from WProfX import trace_parser as profiler


app = Flask(__name__)

@app.route('/')
def initPage():
    return render_template('index.html', name='index')
@app.route('/receiver', methods=['POST'])
def webProfile():
    #print(request.get_data())
    # Insert Profiling part here
    requested_site = request.get_data().decode('utf-8')
    fetch.traceWithInput(requested_site)
    # profiler.analyzeTrace(requested_site.split('/')[-1])
    response = {'status':200, 'site':requested_site}
    # response = make_response('Analysis Finished', 200)
    return jsonify(response)
@app.route('/profiled_result')
def showProfiledResult():
    requested_site = request.get_data().decode('utf-8')
    print(requested_site)
    template_name = '/profiled_result/' + 'www.facebook.com'+ '.html'
    print(template_name)
    return render_template(template_name)

if __name__ == '__main__':
    app.run("0.0.0.0", 5000)

