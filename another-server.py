from flask import Flask, request, render_template, make_response
from flask.ext.restful import Api, Resource, reqparse, abort

import rdflib
from copy import deepcopy

# contacts data
data = [ { "name": "Gary Marchionini",
           "email": "gary@unc.edu" },
         { "name": "Ryan Shaw",
           "email": "ryanshaw@unc.edu" },
         { "name": "Paul Jones",
           "email": "paul@unc.edu" },
         { "name": "Diane Kelly",
           "email": "diane@unc.edu" } ]

schema = rdflib.Namespace("http://schema.org/")

#
# define our (kinds of) resources
#
class ContactListAsJSON(Resource):
    def get(self):
        contacts = deepcopy(data) 
        graph = rdflib.Graph()
        graph.parse("http://aeshin.org:5555/requests.json", format="json-ld")
        for contact in contacts:
            contact["requests"] = []
            for s in graph.subjects(
                    predicate=schema.creator,
                    object=rdflib.Literal(contact["email"])):
                contact["requests"].append(str(s))
        return contacts

#
# assign URL paths to our resources
#
app = Flask(__name__)
api = Api(app)
api.add_resource(ContactListAsJSON, '/contacts.json')

# start the server
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5556, debug=True)

