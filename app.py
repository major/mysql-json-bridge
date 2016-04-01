#!/usr/bin/env python
"""
Copyright 2012 Major Hayden

Licensed under the Apache License, Version 2.0 (the "License"); you may
not use this file except in compliance with the License. You may obtain
a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
License for the specific language governing permissions and limitations
under the License.

MySQL <-> JSON bridge
"""

import datetime
import decimal
import json
import logging
import os
import yaml

from flask import Flask, make_response, Response, request
from functools import wraps
from torndb import Connection

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
    """Decorator to return JSON easily."""
    @wraps(f)
    def inner(*args, **kwargs):
        # Change our datetime columns into strings so we can serialize
        f_return = f(*args, **kwargs)

        if len(f_return) > 1:
            jsonstring = json.dumps(f_return[0], default=json_fixup)
            resp = make_response(jsonstring, *f_return[1:])
            resp.mimetype = 'application/json'
            return resp

        jsonstring = json.dumps(f_return, default=json_fixup)
        return Response(jsonstring, mimetype='application/json')
    return inner


def json_fixup(obj):
    """Perform type transformation on json."""
    if isinstance(obj, datetime.datetime):
        return obj.isoformat()
    if isinstance(obj, decimal.Decimal):
        return float(obj)
    else:
        return None


def read_config():
    """Read Config from config directory."""
    databases = {}
    cfiles = []

    cdir = data_file('conf.d/')
    for dirname, dirnames, filenames in os.walk(cdir):
        for filename in filenames:
            fullpath = os.path.join(dirname, filename)
            cfiles.append(fullpath)

    for cfile in cfiles:
        tmp = {}
        if not cfile.endswith('.yaml'):
            continue
        fh = open(data_file(cfile), 'r')
        db = yaml.load(fh)
        fh.close()

        if db is None:
            continue

        required = [
            'hostname',
            'database',
            'username',
            'password',
            'identifier',
            'enabled'
        ]

        if not all(param in db for param in required):
            continue

        identifier = db.pop("identifier")

        if db['enabled'] != 'True':
            continue

        tmp[identifier] = db

        databases = dict(databases.items() + tmp.items())
    return databases


# Pull the database credentials from our YAML file
def get_db_creds(database):
    """Retrieve DB credentials."""
    databases = read_config()
    config = databases.get(database)

    # If the database doesn't exist in the yaml, we're done
    if not config:
        return False

    # Parse the URL in the .yml file
    try:
        creds = {
            'host': config["hostname"],
            'database': config["database"],
            'user': config["username"],
            'password': config["password"],
        }
    except:
        creds = False

    return creds


# Handles the listing of available databases
@app.route("/list", methods=['GET'])
def return_database_list():
    """Return list of configured databases."""
    databases = read_config()
    data = {'databases': databases.keys()}
    return Response(json.dumps(data), mimetype='application/json')


# This is what receives our SQL queries
@app.route("/query/<database>", methods=['POST', 'GET'])
@jsonify
def do_query(database=None):
    """Perform generic query on database."""
    # Pick up the database credentials
    creds = get_db_creds(database)

    # If we couldn't find corresponding credentials, throw a 404
    if not creds:
        msg = "Unable to find credentials matching {0}."
        return {"ERROR": msg.format(database)}, 404

    # Prepare the database connection
    app.logger.debug("Connecting to %s database (%s)" % (
        database, request.remote_addr))
    db = Connection(**creds)

    # See if we received a query
    sql = request.form.get('sql')
    if not sql:
        sql = request.args.get('sql')
        if not sql:
            return {"ERROR": "SQL query missing from request."}, 400

    # If the query has a percent sign, we need to excape it
    if '%' in sql:
        sql = sql.replace('%', '%%')

    # Attempt to run the query
    try:
        app.logger.info("%s attempting to run \" %s \" against %s database" % (
            request.remote_addr, sql, database))
        results = db.query(sql)
        app.logger.info(results)
    except Exception, e:
        return {"ERROR": ": ".join(str(i) for i in e.args)}, 422

    # Disconnect from the DB
    db.close()

    return {'result': results}


@app.route("/update/<database>", methods=['POST', 'GET'])
@jsonify
def do_update(database=None):
    """Perform databse update."""
    # Pick up the database credentials
    creds = get_db_creds(database)

    # If we couldn't find corresponding credentials, throw a 404
    if not creds:
        msg = "Unable to find credentials matching {0}."
        return {"ERROR": msg.format(database)}, 404

    # Prepare the database connection
    app.logger.debug("Connecting to %s database (%s)" % (
        database, request.remote_addr))
    db = Connection(**creds)

    # See if we received a query
    sql = request.form.get('sql')
    if not sql:
        sql = request.args.get('sql')
        if not sql:
            return {"ERROR": "SQL query missing from request."}, 400

    # If the query has a percent sign, we need to excape it
    if '%' in sql:
        sql = sql.replace('%', '%%')

    # Attempt to run the query
    try:
        app.logger.info("%s attempting to run \" %s \" against %s database" % (
            request.remote_addr, sql, database))
        results = db.update(sql)
        app.logger.info(results)
    except Exception, e:
        return {"ERROR": ": ".join(str(i) for i in e.args)}, 422

    # Disconnect from the DB
    db.close()

    return {'result': results}


if __name__ == "__main__":
    app.run(host='0.0.0.0')
