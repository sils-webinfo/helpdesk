This is an example of a simple web API implemented using
[Flask](http://flask.pocoo.org/) and
[Flask-RESTful](http://flask-restful.readthedocs.org/en/latest/).

To run it:

1. Install required dependencies:
   ```
   $ pip install -r requirements.txt
   ``` 
   [Flask](http://flask.pocoo.org/docs/0.10/installation/#installation)
   and
   [Flask-RESTful](http://flask-restful.readthedocs.org/en/latest/installation.html) to run `server.py` 
   and [RDFLib](http://rdflib.readthedocs.org/en/latest/) and [JSONLD for RDFLib](https://github.com/RDFLib/rdflib-jsonld) to run the `extractdata.py` script or the `another-server.py` service.

2. Run the helpdesk server:
   ```
   $ python server.py
   ```
   Alternatively, you can access the service running here: http://aeshin.org:5555/requests
   
3. Use the `extractdata.py` script to examine the triples found in various representations of the helpdesk resources.
   
   RDFa/microdata for the list of help requests:
   ```
   $ python extractdata.py http://aeshin.org:5555/requests
   ```
   JSON-LD for the list of help requests:
   ```
   $ python extractdata.py http://aeshin.org:5555/requests.json
   ```
   RDFa/microdata for an individual help request:
   ```
   $ python extractdata.py http://aeshin.org:5555/request/fhs6jo
   ```
   JSON-LD for an individual help request:
   ```
   $ python extractdata.py http://aeshin.org:5555/request/fhs6jo.json
   ```

4. Run the contacts server for an example of a service calling another service:
   ```
   $ python another-server.py
   ```
   Alternatively, you can access the service running here: http://aeshin.org:5556/contacts.json
   
