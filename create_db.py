#!flask/bin/python
from migrate.versioning import api
from config import SQLALCHEMY_DATABASE_URI
from config import SQLALCHEMY_MIGRATE_REPO
from app import db
from app.models import Role, Setting
import os.path
db.create_all()
# create initial user roles and turn off maintenance mode
admin_role = Role('Administrator', 'Administrator')
user_role = Role('User', 'User')
maintenance_setting = Setting('maintenance', 'False')
db.session.add(admin_role)
db.session.add(user_role)
db.session.add(maintenance_setting)
db.session.commit()
if not os.path.exists(SQLALCHEMY_MIGRATE_REPO):
    api.create(SQLALCHEMY_MIGRATE_REPO, 'database repository')
    api.version_control(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO)
else:
    api.version_control(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO, api.version(SQLALCHEMY_MIGRATE_REPO))