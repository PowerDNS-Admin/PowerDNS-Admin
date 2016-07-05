#!flask/bin/python
from migrate.versioning import api
from config import SQLALCHEMY_DATABASE_URI
from config import SQLALCHEMY_MIGRATE_REPO
from app import db
from app.models import Role, Setting
import os.path
import time
import sys

# Create schema
if os.environ.get('WAITFOR_DB') is None:
    db.create_all()
else:
    for i in range(0, int(os.environ.get('WAITFOR_DB'))):
        try:
            db.create_all()
            break
        except:
            print("INFO: Wait for database server")
            sys.stdout.flush()
            time.sleep(1)
            continue
        print("ERROR: Couldn't connect to database server")
        exit(1)

# create initial user roles and turn off maintenance mode
admin_role = Role('Administrator', 'Administrator')
user_role = Role('User', 'User')
maintenance_setting = Setting('maintenance', 'False')
fullscreen_layout_setting = Setting('fullscreen_layout', 'True')
record_helper_setting = Setting('record_helper', 'True')
default_table_size_setting = Setting('default_record_table_size', '15')

# Check if record already exists
if not db.session.query(Role).filter_by(name="Administrator").first():
    db.session.add(admin_role)
if not db.session.query(Role).filter_by(name="User").first():
    db.session.add(user_role)
if not db.session.query(Setting).filter_by(name="maintenance").first():
    db.session.add(maintenance_setting)
if not db.session.query(Setting).filter_by(name="fullscreen_layout").first():
    db.session.add(fullscreen_layout_setting)
if not db.session.query(Setting).filter_by(name="record_helper").first():
    db.session.add(record_helper_setting)
if not db.session.query(Setting).filter_by(name="default_record_table_size").first():
    db.session.add(default_table_size_setting)
db_commit = db.session.commit()

if not os.path.exists(SQLALCHEMY_MIGRATE_REPO):
    api.create(SQLALCHEMY_MIGRATE_REPO, 'database repository')
    api.version_control(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO)
elif db_commit is not None:
    api.version_control(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO, api.version(SQLALCHEMY_MIGRATE_REPO))
