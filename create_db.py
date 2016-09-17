#!/usr/bin/env python

from migrate.versioning import api
from config import SQLALCHEMY_DATABASE_URI
from config import SQLALCHEMY_MIGRATE_REPO
from app import db
from app.models import Role, Setting
import os.path
import time
import sys

def start():
    wait_time = get_waittime_from_env()

    if not connect_db(wait_time):
        print("ERROR: Couldn't connect to database server")
        exit(1)

    init_records()

def get_waittime_from_env():
    return int(os.environ.get('WAITFOR_DB', 1))

def connect_db(wait_time):
    for i in range(0, wait_time):
        print("INFO: Wait for database server")
        sys.stdout.flush()
        try:
            db.create_all()
            return True
        except:
            time.sleep(1)

    return False

def init_roles(db, role_names):

    # Get key name of data
    name_of_roles = [r.name for r in role_names]

    # Query to get current data
    rows = db.session.query(Role).filter(Role.name.in_(name_of_roles)).all()
    name_of_rows = [r.name for r in rows]

    # Check which data that need to insert
    roles = [r for r in role_names if r.name not in name_of_rows]

    # Insert data
    for role in roles:
        db.session.add(role)

def init_settings(db, setting_names):

    # Get key name of data
    name_of_settings = [r.name for r in setting_names]

    # Query to get current data
    rows = db.session.query(Setting).filter(Setting.name.in_(name_of_settings)).all()

    # Check which data that need to insert
    name_of_rows = [r.name for r in rows]
    settings = [r for r in setting_names if r.name not in name_of_rows]

    # Insert data
    for setting in settings:
        db.session.add(setting)

def init_records():
    # Create initial user roles and turn off maintenance mode
    init_roles(db, [
        Role('Administrator', 'Administrator'),
        Role('User', 'User')
    ])
    init_settings(db, [
        Setting('maintenance', 'False'),
        Setting('fullscreen_layout', 'True'),
        Setting('record_helper', 'True'),
        Setting('login_ldap_first', 'True'),
        Setting('default_record_table_size', '15'),
        Setting('default_domain_table_size', '10')
    ])

    db_commit = db.session.commit()
    commit_version_control(db_commit)

def commit_version_control(db_commit):
    if not os.path.exists(SQLALCHEMY_MIGRATE_REPO):
        api.create(SQLALCHEMY_MIGRATE_REPO, 'database repository')
        api.version_control(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO)
    elif db_commit is not None:
        api.version_control(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO, api.version(SQLALCHEMY_MIGRATE_REPO))

if __name__ == '__main__':
    start()
