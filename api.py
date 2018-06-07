from flask import Flask, request, jsonify
from flask.ext.restful import Resource, Api
import uuid
from WProfX import main as fetch
from WProfX import trace_parser as profiler
import _thread
import os

app = Flask(__name__)
api = Api(app)
urls_to_be_profiled = {}
class ProfilingSites(Resource):

    def profiling_process(self,url):
        requested_site = urls_to_be_profiled[uuid.uuid3(name=url, namespace=uuid.NAMESPACE_OID)]
        fetch.traceWithInput(requested_site)
        profiler.analyzeTrace(requested_site.split('/')[-1])
        response = {'status':200, 'site':requested_site}
        return jsonify(response)

    def reading_profiled_result(self, url):
        requested_site = urls_to_be_profiled[uuid.uuid3(name=url, namespace=uuid.NAMESPACE_OID)]
        json_file_path = ''.join([os.path.normpath(os.path.dirname(os.path.realpath(__file__))), '/WProfX', '/graphs/',
                        '0_', requested_site.split('/')[-1].replace(" ", ""), '.json'])
        with open(json_file_path, 'r') as f:
            return jsonify(f.read())

    def put_url_to_be_profiled(self, url):
        urls_to_be_profiled[uuid.uuid3(name=url, namespace=uuid.NAMESPACE_OID)] = url
        return "URL {} was accepted! Will be profiled".format(url)

    def get_profiled(self, url):
        # Start a new thread to process
        try:
            _thread.start_new_thread(self.profiling_process, (url))
        except Exception as e:
            return jsonify({'status':400, 'info':str(e)})

    def get_profiled_data_json(self, url):


    def get_profiled_graph(self,url):



api.add_resource(ProfilingSites, '/<string:url>')