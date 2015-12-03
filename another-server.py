from flask import Flask, redirect
from flask.ext.restful import Api, Resource

from copy import deepcopy

from twitter import Twitter
twitter = Twitter()


# contacts data
data = [{'name': 'Gary Marchionini',
         'email': 'gary@unc.edu',
         'twitter': 'marchionini'},
        {'name': 'Ryan Shaw',
         'email': 'ryanshaw@unc.edu',
         'twitter': 'rybesh'},
        {'name': 'Paul Jones',
         'email': 'paul@unc.edu',
         'twitter': 'smalljones'},
        {'name': 'Diane Kelly',
         'email': 'diane@unc.edu'}]


# Define our contacts list resource.
class ContactListAsJSON(Resource):
    def get(self):
        contacts = deepcopy(data)
        for contact in contacts:
            if 'twitter' in contact:
                tweets = twitter.search('from:%s' % contact['twitter'])
                if len(tweets) > 0:
                    contact['last_tweet'] = tweets[0]['text']
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
