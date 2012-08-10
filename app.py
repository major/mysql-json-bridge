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

import datetime
import json
import logging
import os
from urlparse import urlparse
import yaml


from tornado.database import Connection
from flask import Flask, Response, abort, request


app = Flask(__name__)
app.debug = True


# Helps us find non-python files installed by setuptools
def data_file(fname):
    """Return the path to a data file of ours."""
    return os.path.join(os.path.split(__file__)[0], fname)

if not app.debug:
    logyaml = ""
    with open(data_file('config/log.yml'), 'r') as f:
        logyaml = yaml.load(f)
    try:
        formatter = logging.Formatter('%(asctime)s - %(message)s')
        if logyaml['type'] == "file":
            from logging.handlers import RotatingFileHandler
            file_handler = RotatingFileHandler(
                logyaml['logfile'], backupCount=logyaml['backupCount'])
            file_handler.setLevel(logging.INFO)
            file_handler.setFormatter(formatter)
            app.logger.addHandler(file_handler)
        elif logyaml['type'] == 'syslog':
            from logging.handlers import SysLogHandler
            syslog_handler = SysLogHandler()
            syslog_handler.setLevel(logging.INFO)
            syslog_handler.setFormatter(formatter)
            app.logger.addHandler(syslog_handler)
    except:
        pass


# Decorator to return JSON easily
def jsonify(f):
    def inner(*args, **kwargs):
        # Change our datetime columns into strings so we can serialize
        dthandler = lambda obj: obj.isoformat() if isinstance(obj,
            datetime.datetime) else None
        jsonstring = json.dumps(f(*args, **kwargs), default=dthandler)
        return Response(jsonstring, mimetype='application/json')
    return inner


def read_config():
    with open(data_file('config/databases.yml'), 'r') as f:
        databases = yaml.load(f)
    return databases


# Pull the database credentials from our YAML file
def get_db_creds(database):
    databases = read_config()
    mysql_uri = databases.get(database)

    # If the database doesn't exist in the yaml, we're done
    if not mysql_uri:
        return False

    # Parse the URL in the .yml file
    try:
        o = urlparse(mysql_uri)
        creds = {
            'host':         o.hostname,
            'database':     o.path[1:],
            'user':         o.username,
            'password':     o.password,
        }
    except:
        creds = False

    return creds


# Handles the listing of available databases
@app.route("/list", methods=['GET'])
def return_database_list():
    databases = read_config()
    data = {'databases': databases.keys()}
    return Response(json.dumps(data), mimetype='application/json')


# This is what receives our SQL queries
@app.route("/query/<database>", methods=['POST'])
@jsonify
def do_query(database=None):
    # Pick up the database credentials
    # app.logger.warning("%s requesting access to %s database" % (
    #     request.remote_addr, database))
    creds = get_db_creds(database)

    # If we couldn't find corresponding credentials, throw a 404
    if creds == False:
        return {"ERROR": "Unable to find credentials matching %s." % database}
        abort(404)

    # Prepare the database connection
    app.logger.debug("Connecting to %s database (%s)" % (
        database, request.remote_addr))
    db = Connection(**creds)

    # See if we received a query
    sql = request.form.get('sql')
    if not sql:
        return {"ERROR": "SQL query missing from request."}

    # If the query has a percent sign, we need to excape it
    if '%' in sql:
        sql = sql.replace('%', '%%')

    # Attempt to run the query
    try:
        app.logger.info("%s attempting to run \" %s \" against %s database" % (
            request.remote_addr, sql, database))
        results = db.query(sql)
    except Exception, e:
        return {"ERROR": ": ".join(str(i) for i in e.args)}

    # Disconnect from the DB
    db.close()

    return {'result': results}


if __name__ == "__main__":
    app.run(host='0.0.0.0')
