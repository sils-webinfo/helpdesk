from flask import Flask, redirect
from flask.ext.restful import Api, Resource

import rdflib
from copy import deepcopy

# contacts data
data = [{"name": "Gary Marchionini",
         "email": "gary@unc.edu"},
        {"name": "Ryan Shaw",
         "email": "ryanshaw@unc.edu"},
        {"name": "Paul Jones",
         "email": "paul@unc.edu"},
        {"name": "Diane Kelly",
         "email": "diane@unc.edu"}]

schema = rdflib.Namespace("http://schema.org/")


# Define our contacts list resource.
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


# Assign URL paths to our resources.
app = Flask(__name__)
api = Api(app)
api.add_resource(ContactListAsJSON, '/contacts.json')


# Redirect from the index to the list of contacts.
@app.route('/')
def index():
    return redirect(api.url_for(ContactListAsJSON), code=303)


# Start the server.
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5556, debug=True)
