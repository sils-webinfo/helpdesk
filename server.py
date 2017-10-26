# First we import parts of the frameworks we're using:
#
# Flask <http://flask.pocoo.org> is a simple framework for building web
# applications in Python. It handles basic things like parsing incoming
# HTTP requests and generating responses.
#
# Flask-RESTful <https://flask-restful.readthedocs.io/> is an add-on to Flask
# that makes it easier to build web applications that adhere to the REST
# architectural style.

from flask import (Flask, Response, request, render_template, make_response,
                   redirect)
from flask_restful import Api, Resource, reqparse, abort

# Next we import some standard Python libraries and functions:
#
# json <https://docs.python.org/3/library/json.html> for loading a JSON file
# from disk (our "database") into memory.
#
# random <https://docs.python.org/3/library/random.html> and string
# <https://docs.python.org/3/library/string.html> to help us generate
# unique IDs for help tickets from lowercase letters and digits.
#
# datetime <https://docs.python.org/3/library/datetime.html> to help us
# generate timestamps for help tickets.
#
# wraps <https://docs.python.org/3/library/functools.html#functools.wraps>
# is just a convenience function that will help us implement authentication.

import json
import random
import string
from datetime import datetime
from functools import wraps

# Define some constants for our priority levels.
# These are the values that the "priority" property can take on a help ticket.
PRIORITIES = ('closed', 'low', 'normal', 'high')

# Load data from disk.
# This simply loads the data from our "database," which is just a JSON file.
with open('data.jsonld') as data:
    data = json.load(data)


# The next three functions implement simple authentication.

# Check that username and password are OK; DON'T DO THIS FOR REAL
def check_auth(username, password):
    return username == 'admin' and password == 'secret'


# Issue an authentication challenge
def authenticate():
    return Response(
        'Please authenticate yourself', 401,
        {'WWW-Authenticate': 'Basic realm="helpdesk"'})


# Decorator for methods that require authentication
def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated


# The following are three  helper functions used in our resource classes.

# Generate a unique ID for a new help ticket.
# By default this will consist of six lowercase numbers and letters.
def generate_id(size=6, chars=string.ascii_lowercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


# Respond with 404 Not Found if no help ticket with the specified ID exists.
def error_if_helpticket_not_found(helpticket_id):
    if helpticket_id not in data['helptickets']:
        message = "No help ticket with ID: {}".format(helpticket_id)
        abort(404, message=message)


# Filter and sort a list of helptickets.
def filter_and_sort_helptickets(query='', sort_by='time'):

    # Returns True if the query string appears in the help ticket's
    # title or description.
    def matches_query(item):
        (helpticket_id, helpticket) = item
        text = helpticket['title'] + helpticket['description']
        return query.lower() in text

    # Returns the help ticket's value for the sort property (which by
    # default is the "time" property).
    def get_sort_value(item):
        (helpticket_id, helpticket) = item
        return helpticket[sort_by]

    filtered_helptickets = filter(matches_query, data['helptickets'].items())

    return sorted(filtered_helptickets, key=get_sort_value, reverse=True)


# Now we define three incoming HTTP request parsers using the Flask-RESTful
# framework <https://flask-restful.readthedocs.io/en/latest/reqparse.html>.
#
# The first (new_helpticket_parser) parses incoming POST requests and checks
# that they have the required values.
#
# The second (update_helpticket_parser) parses incoming PATCH requests and
# checks that they have the required values.
#
# The third (query_parser) parses incoming GET requests to get the parameters
# for sorting and filtering the list of help tickets.

# Helper function new_helpticket_parser. Raises an error if the string x
# is empty (has zero length).
def nonempty_string(x):
    s = str(x)
    if len(x) == 0:
        raise ValueError('string is empty')
    return s


# Specify the data necessary to create a new help ticket.
# "from", "title", and "description" are all required values.
new_helpticket_parser = reqparse.RequestParser()
for arg in ['from', 'title', 'description']:
    new_helpticket_parser.add_argument(
        arg, type=nonempty_string, required=True,
        help="'{}' is a required value".format(arg))


# Specify the data necessary to update an existing help ticket.
# Only the priority and comments can be updated.
update_helpticket_parser = reqparse.RequestParser()
update_helpticket_parser.add_argument(
    'priority', type=int, default=PRIORITIES.index('normal'))
update_helpticket_parser.add_argument(
    'comment', type=str, default='')


# Specify the parameters for filtering and sorting help tickets.
# See `filter_and_sort_helptickets` above.
query_parser = reqparse.RequestParser()
query_parser.add_argument(
    'query', type=str, default='')
query_parser.add_argument(
    'sort_by', type=str, choices=('priority', 'time'), default='time')


# Then we define a couple of helper functions for inserting data into HTML
# templates (found in the templates/ directory). See
# <http://flask.pocoo.org/docs/latest/quickstart/#rendering-templates>.

# Given the data for a help ticket, generate an HTML representation
# of that help ticket.
def render_helpticket_as_html(helpticket):
    return render_template(
        'helpticket+microdata+rdfa.html',
        helpticket=helpticket,
        priorities=reversed(list(enumerate(PRIORITIES))))


# Given the data for a list of help tickets, generate an HTML representation
# of that list.
def render_helpticket_list_as_html(helptickets):
    return render_template(
        'helptickets+microdata+rdfa.html',
        helptickets=helptickets,
        priorities=PRIORITIES)


# Now we can start defining our resource classes. We define four classes:
# HelpTicket, HelpTicketAsJSON, HelpTicketList, and HelpTicketListAsJSON.
# All of them accept GET requests. HelpTicket also accepts PATCH requests,
# and HelpTicketList also accepts POST requests.

# Define our help ticket resource.
class HelpTicket(Resource):

    # If a help ticket with the specified ID does not exist,
    # respond with a 404, otherwise respond with an HTML representation.
    def get(self, helpticket_id):
        error_if_helpticket_not_found(helpticket_id)
        return make_response(
            render_helpticket_as_html(
                data['helptickets'][helpticket_id]), 200)

    # If a help ticket with the specified ID does not exist,
    # respond with a 404, otherwise update the help ticket and respond
    # with the updated HTML representation.
    def patch(self, helpticket_id):
        error_if_helpticket_not_found(helpticket_id)
        helpticket = data['helptickets'][helpticket_id]
        update = update_helpticket_parser.parse_args()
        helpticket['priority'] = update['priority']
        if len(update['comment'].strip()) > 0:
            helpticket.setdefault('comments', []).append(update['comment'])
        return make_response(
            render_helpticket_as_html(helpticket), 200)


# Define a resource for getting a JSON representation of a help ticket.
class HelpTicketAsJSON(Resource):

    # If a help ticket with the specified ID does not exist,
    # respond with a 404, otherwise respond with a JSON representation.
    def get(self, helpticket_id):
        error_if_helpticket_not_found(helpticket_id)
        helpticket = data['helptickets'][helpticket_id]
        helpticket['@context'] = data['@context']
        return helpticket


# Define our help ticket list resource.
class HelpTicketList(Resource):

    # Respond with an HTML representation of the help ticket list, after
    # applying any filtering and sorting parameters.
    def get(self):
        query = query_parser.parse_args()
        return make_response(
            render_helpticket_list_as_html(
                filter_and_sort_helptickets(**query)), 200)

    # Add a new help ticket to the list, and respond with an HTML
    # representation of the updated list.
    def post(self):
        helpticket = new_helpticket_parser.parse_args()
        helpticket_id = generate_id()
        helpticket['@id'] = 'request/' + helpticket_id
        helpticket['@type'] = 'helpdesk:HelpTicket'
        helpticket['time'] = datetime.isoformat(datetime.now())
        helpticket['priority'] = PRIORITIES.index('normal')
        data['helptickets'][helpticket_id] = helpticket
        return make_response(
            render_helpticket_list_as_html(
                filter_and_sort_helptickets()), 201)


# Define a resource for getting a JSON representation of the help ticket list.
class HelpTicketListAsJSON(Resource):
    def get(self):
        return data


# After defining our resource classes, we define how URLs are assigned to
# resources by mapping resource classes to URL patterns.

app = Flask(__name__)
api = Api(app)
api.add_resource(HelpTicketList, '/tickets')
api.add_resource(HelpTicketListAsJSON, '/tickets.json')
api.add_resource(HelpTicket, '/ticket/<string:helpticket_id>')
api.add_resource(HelpTicketAsJSON, '/ticket/<string:helpticket_id>.json')


# There is no resource mapped to the root path (/), so if a request comes in
# for that, redirect to the HelpTicketList resource.

@app.route('/')
def index():
    return redirect(api.url_for(HelpTicketList), code=303)


# Finally we add some headers to all of our HTTP responses which will allow
# JavaScript loaded from other domains and running in the browser to load
# representations of our resources (for security reasons, this is disabled
# by default.

@app.after_request
def after_request(response):
    response.headers.add(
        'Access-Control-Allow-Origin', '*')
    response.headers.add(
        'Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add(
        'Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE')
    return response


# Now we can start the server.

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5555, debug=True)
