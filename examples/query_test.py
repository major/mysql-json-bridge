#!/usr/bin/env python
import json
import pprint
import requests


payload = {'sql': 'SELECT * FROM information_schema.tables'}
url = "http://localhost:5000/query/my_database"

r = requests.post(url, data=payload)

print r.status_code
try:
    pprint.pprint(json.loads(r.text))
except:
    pprint.pprint(r.text)
