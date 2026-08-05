from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
domain_apikey = db.Table(
    'domain_apikey',
    db.Column('domain_id', db.Integer, db.ForeignKey('domain.id')),
    db.Column('apikey_id', db.Integer, db.ForeignKey('apikey.id')),
    db.Index('ix_domain_apikey_apikey_id_domain_id',
             'apikey_id', 'domain_id'))
