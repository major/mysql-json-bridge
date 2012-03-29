mysql-json-bridge
=================
Talk to MySQL using HTTP POST and get result sets via JSON.

Key features
------------

* Use any scripting/programming language to talk to MySQL
* Make a single endpoint for multiple environments and database servers
* Use any authentication mechanism your web server supports for database access
* Handle queries through HTTP load balancers

Installation & Startup
----------------------
Install a few prerequisites:

    pip install flask pyyaml
    # requests is optional, but you need it to use the quick test file
    pip install requests 

Get the source:

    git clone http://github.com/rackerhacker/mysql-json-bridge
    cd mysql-json-bridge
    python app.py

Configuration
-------------
You'll need to tell the bridge where it can find its databases.  Look inside `config/environments.yml` for an example.

The base element is the environment.  In the example YAML file provided, the environments are _prod_ and _preprod_.  Within each environment are two databases along with the data needed to access each database.

Usage
-----
Look inside the `examples/query_test.py` file for a quick example.  To issue a query to the bridge, simply make an HTTP POST to the appropriate URL.  Your URL should be something like this:

    http://localhost:5000/<environment>/<database>

Our example YAML file has a _sales_ database inside the _prod_ environment.  If you wanted to issue a query there, ensure that the URL is:

    http://localhost:5000/prod/sales

After you adjust the `examples/query_test.py` file, you should have something like this:

    #!/usr/bin/env python
    import json
    import pprint
    import requests


    payload = {'sql': 'SELECT * FROM invoices WHERE paid=0'}
    url = "http://localhost:5000/prod/sales"

    r = requests.post(url, data=payload)

    print r.status_code
    try:
        pprint.pprint(json.loads(r.text))
    except:
        pprint.pprint(r.text)

*IMPORTANT* security considerations
-----------------------------------
**The base mysql-json-bridge server doesn't do any query filtering nor does it do any authentication.  You'd need to configure that yourself within your web server.**

Also, be very careful with the user you configure in your `environments.yml`.  If the user has write access to your database, people could issue UPDATE and DELETE statements through the bridge.

If you create read-only MySQL users for the bridge to use, **ensure that those users have read access *only* to the databases that you specify.**  Giving global read access to a user allows them to read your `mysql.user` table which contains hashed passwords.  *This could lead to a very bad experience.*

Got improvements?  Found a bug?
-------------------------------
Issue a pull request or open an issue in GitHub.  I'm still learning Python and I'm sure there are some better ways to do things than I'm currently doing them.  I appreciate and welcome all feedback you have!

Thanks!  
Major Hayden  
major at mhtx dot net  
