#!/usr/bin/env python3
import sys
sys.path.insert(0, '/var/www/powerdns-admin/')

activate_this = '/var/www/powerdns-admin/flask/bin/activate_this.py'
with open(activate_this) as file_:
        exec(file_.read(), dict(__file__=activate_this))

from powerdnsadmin import create_app
application = create_app(config='../configs/production.py')
application.secret_key = "secret"
