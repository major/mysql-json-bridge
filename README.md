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
You'll need to tell the bridge where it can find its databases.  Make a file in `config/databases.yml` with your database servers in a standard MySQL URI format:

    --- 
    production-sales: "mysql://myuser:mysecretpass@10.0.1.10/salesdb"
    staging-sales: "mysql://myuser:mysecretpass@10.0.2.10/salesdb"

Optionally you can use the conf.d with separate database configuration files:

    # conf.d/database1.yml
    ---
    identifier: 'prod.database1'
    scheme: 'mysql'
    username: 'database1'
    password: 'secret_password'
    database: 'database1'
    hostname: 'database1.domain.com'
    enabled: 'True'

    # conf.d/database2.yml
    ---
    identifier: 'staging.database2'
    scheme: 'mysql'
    username: 'database2'
    password: 'secret_password'
    database: 'database2'
    hostname: 'database2.domain.com'
    enabled: 'True'

Usage
-----
Look inside the `examples/query_test.py` file for a quick example.  To issue a query to the bridge, simply make an HTTP POST to the appropriate URL.  Your URL should be something like this:

    http://localhost:5000/query/<database>

You can also test with curl:

    curl http://localhost:5000/query/production-sales -X POST -d 'sql=SELECT version()'

Example wsgi file for usage with a web server:

    # mysql-json-bridge.wsgi
    import sys
    sys.path.insert(0, '/path/to/mysql-json-bridge/')
    from app import app as application

*IMPORTANT* security considerations
-----------------------------------
**The base mysql-json-bridge server doesn't do any query filtering nor does it do any authentication.  You'd need to configure that yourself within your web server.**

Also, be very careful with the user you configure in your `environments.yml`.  If the user has write access to your database, people could issue UPDATE and DELETE statements through the bridge.

If you create read-only MySQL users for the bridge to use, **ensure that those users have read access *only* to the databases that you specify.**  Giving global read access to a user allows them to read your `mysql.user` table which contains hashed passwords.  *This could lead to a very bad experience.*

Got improvements?  Found a bug?
-------------------------------
Issue a pull request or open an issue in GitHub.  I'm still learning Python and I'm sure there are some better ways to do things than I'm currently doing them.  I appreciate and welcome all feedback you have!
