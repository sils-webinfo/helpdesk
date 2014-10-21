from flask import Flask, render_template, make_response
from flask.ext import restful
import json

app = Flask(__name__)
api = restful.Api(app)

with open("data.json") as data:
    requests = json.load(data)

def error_if_request_not_found(request_id):
    if request_id not in requests:
        message = "Request {} doesn't exist".format(request_id)    
        restful.abort(404, message)

class HelpRequest(restful.Resource):
    def get(self, request_id):
        error_if_request_not_found(request_id)
        return make_response(render_template(
            "request.html", request=requests[request_id]), 200)

class HelpRequestAsJSON(restful.Resource):
    def get(self, request_id):
        error_if_request_not_found(request_id)
        return requests[request_id]
    
class HelpRequestList(restful.Resource):
    def get(self):
        return make_response(render_template(
            "requests.html", requests=requests), 200)

class HelpRequestListAsJSON(restful.Resource):
    def get(self):
        return requests

api.add_resource(HelpRequestList, '/requests')
api.add_resource(HelpRequestListAsJSON, '/requests.json')
api.add_resource(HelpRequest, '/request/<string:request_id>')
api.add_resource(HelpRequestAsJSON, '/request/<string:request_id>.json')

if __name__ == '__main__':
    app.run(debug=True)

