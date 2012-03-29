#!/usr/bin/env python
#
# Copyright 2012 Major Hayden
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""MySQL <-> JSON bridge"""

from tornado.database import Connection
from flask import Flask, g, render_template, Response, abort, request
import datetime
import json
import os
import sys
import yaml

app = Flask(__name__)
app.debug = True

# Helps us find non-python files installed by setuptools
def data_file(fname):
    """Return the path to a data file of ours."""
    return os.path.join(os.path.split(__file__)[0], fname)

# Decorator to return JSON easily
def jsonify(f):
    def inner(*args, **kwargs):
        # Change our datetime columns into strings so we can serialize
        dthandler = lambda obj: obj.isoformat() if isinstance(obj, 
            datetime.datetime) else None
        jsonstring = json.dumps(f(*args, **kwargs), default=dthandler)
        return Response(jsonstring, mimetype='application/json')
    return inner

# Pull the database credentials from our YAML file
def get_db_creds(environment, database):
    with open(data_file('config/environments.yml'), 'r') as f:
        environments = yaml.load(f)
    try:
        creds = environments[environment][database]
    except:
        creds = False
    return creds

# Any request we're not looking for should get a 400
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    abort(400)

# This is what receives our SQL queries
@app.route("/<environment>/<database>", methods=['POST'])
@jsonify
def index(environment=None, database=None):
    # Pick up the database credentials
    creds = get_db_creds(environment, database)

    # If we couldn't find corresponding credentials, throw a 404
    if creds == False:
        abort(404)

    # Connect to the database and run the query
    try:
        db = Connection(**creds)
    except:
        abort(500)
    try:
        sql = request.form['sql'].replace(r'%',r'%%')
        results = db.query(sql)
    except Exception as (errno, errstr):
        return (errno, errstr)

    # Disconnect from the DB
    db.close()

    return results

if __name__ == "__main__":
    app.run(host='0.0.0.0')
