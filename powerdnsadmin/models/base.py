from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
domain_apikey = db.Table(
    'domain_apikey',
    db.Column('domain_id', db.Integer, db.ForeignKey('domain.id')),
    db.Column('apikey_id', db.Integer, db.ForeignKey('apikey.id')))
