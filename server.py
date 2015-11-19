from flask import Flask, render_template, make_response, redirect
from flask.ext.restful import Api, Resource, reqparse, abort

import json
import string
import random
from datetime import datetime

# Define our priority levels.
# These are the values that the "priority" property can take on a help request.
PRIORITIES = ('closed', 'low', 'normal', 'high')

# Load data from disk.
# This simply loads the data from our "database," which is just a JSON file.
with open('data.jsonld') as data:
    data = json.load(data)


# Generate a unique ID for a new help request.
# By default this will consist of six lowercase numbers and letters.
def generate_id(size=6, chars=string.ascii_lowercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


# Respond with 404 Not Found if no help request with the specified ID exists.
def error_if_helprequest_not_found(helprequest_id):
    if helprequest_id not in data['helprequests']:
        message = "No help request with ID: {}".format(helprequest_id)
        abort(404, message=message)


# Filter and sort a list of helprequests.
def filter_and_sort_helprequests(query='', sort_by='time'):

    # Returns True if the query string appears in the help request's
    # title or description.
    def matches_query(item):
        (helprequest_id, helprequest) = item
        text = helprequest['title'] + helprequest['description']
        return query.lower() in text

    # Returns the help request's value for the sort property (which by
    # default is the "time" property).
    def get_sort_value(item):
        (helprequest_id, helprequest) = item
        return helprequest[sort_by]

    filtered_helprequests = filter(matches_query, data['helprequests'].items())

    return sorted(filtered_helprequests, key=get_sort_value, reverse=True)


# Given the data for a help request, generate an HTML representation
# of that help request.
def render_helprequest_as_html(helprequest):
    return render_template(
        'helprequest+microdata+rdfa.html',
        helprequest=helprequest,
        priorities=reversed(list(enumerate(PRIORITIES))))


# Given the data for a list of help requests, generate an HTML representation
# of that list.
def render_helprequest_list_as_html(helprequests):
    return render_template(
        'helprequests+microdata+rdfa.html',
        helprequests=helprequests,
        priorities=PRIORITIES)


# Raises an error if the string x is empty (has zero length).
def nonempty_string(x):
    s = str(x)
    if len(x) == 0:
        raise ValueError('string is empty')
    return s


# Specify the data necessary to create a new help request.
# "from", "title", and "description" are all required values.
new_helprequest_parser = reqparse.RequestParser()
for arg in ['from', 'title', 'description']:
    new_helprequest_parser.add_argument(
        arg, type=nonempty_string, required=True,
        help="'{}' is a required value".format(arg))


# Specify the data necessary to update an existing help request.
# Only the priority and comments can be updated.
update_helprequest_parser = reqparse.RequestParser()
update_helprequest_parser.add_argument(
    'priority', type=int, default=PRIORITIES.index('normal'))
update_helprequest_parser.add_argument(
    'comment', type=str, default='')


# Specify the parameters for filtering and sorting help requests.
# See `filter_and_sort_helprequests` above.
query_parser = reqparse.RequestParser()
query_parser.add_argument(
    'query', type=str, default='')
query_parser.add_argument(
    'sort_by', type=str, choices=('priority', 'time'), default='time')


# Define our help request resource.
class HelpRequest(Resource):

    # If a help request with the specified ID does not exist,
    # respond with a 404, otherwise respond with an HTML representation.
    def get(self, helprequest_id):
        error_if_helprequest_not_found(helprequest_id)
        return make_response(
            render_helprequest_as_html(
                data['helprequests'][helprequest_id]), 200)

    # If a help request with the specified ID does not exist,
    # respond with a 404, otherwise update the help request and respond
    # with the updated HTML representation.
    def patch(self, helprequest_id):
        error_if_helprequest_not_found(helprequest_id)
        helprequest = data['helprequests'][helprequest_id]
        update = update_helprequest_parser.parse_args()
        helprequest['priority'] = update['priority']
        if len(update['comment'].strip()) > 0:
            helprequest.setdefault('comments', []).append(update['comment'])
        return make_response(
            render_helprequest_as_html(helprequest), 200)


# Define a resource for getting a JSON representation of a help request.
class HelpRequestAsJSON(Resource):

    # If a help request with the specified ID does not exist,
    # respond with a 404, otherwise respond with a JSON representation.
    def get(self, helprequest_id):
        error_if_helprequest_not_found(helprequest_id)
        helprequest = data['helprequests'][helprequest_id]
        helprequest['@context'] = data['@context']
        return helprequest


# Define our help request list resource.
class HelpRequestList(Resource):

    # Respond with an HTML representation of the help request list, after
    # applying any filtering and sorting parameters.
    def get(self):
        query = query_parser.parse_args()
        return make_response(
            render_helprequest_list_as_html(
                filter_and_sort_helprequests(**query)), 200)

    # Add a new help request to the list, and respond with an HTML
    # representation of the updated list.
    def post(self):
        helprequest = new_helprequest_parser.parse_args()
        helprequest_id = generate_id()
        helprequest['@id'] = 'request/' + helprequest_id
        helprequest['@type'] = 'helpdesk:HelpRequest'
        helprequest['time'] = datetime.isoformat(datetime.now())
        helprequest['priority'] = PRIORITIES.index('normal')
        data['helprequests'][helprequest_id] = helprequest
        return make_response(
            render_helprequest_list_as_html(
                filter_and_sort_helprequests()), 201)


# Define a resource for getting a JSON representation of the help request list.
class HelpRequestListAsJSON(Resource):
    def get(self):
        return data


# Assign URL paths to our resources.
app = Flask(__name__)
api = Api(app)
api.add_resource(HelpRequestList, '/requests')
api.add_resource(HelpRequestListAsJSON, '/requests.json')
api.add_resource(HelpRequest, '/request/<string:helprequest_id>')
api.add_resource(HelpRequestAsJSON, '/request/<string:helprequest_id>.json')


# Redirect from the index to the list of help requests.
@app.route('/')
def index():
    return redirect(api.url_for(HelpRequestList), code=303)


# Start the server.
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5555, debug=True)
