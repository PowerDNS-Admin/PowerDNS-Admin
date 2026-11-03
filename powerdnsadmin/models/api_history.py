from datetime import datetime

from .base import db


class ApiHistory(db.Model):
    """One row for each request under /api.

    user_id and apikey_id are copies taken at request time. They are not
    foreign keys, so deleting a user or an API key leaves the audit row and
    the recorded id in place. Credential material is not stored in this table.
    """

    __tablename__ = 'api_history'

    id = db.Column(db.Integer, primary_key=True)
    created_on = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    method = db.Column(db.String(16), nullable=False)
    path = db.Column(db.String(512), nullable=False)
    query_string = db.Column(db.Text(), nullable=True)
    status_code = db.Column(db.Integer, nullable=True)
    remote_addr = db.Column(db.String(255), nullable=True)
    host = db.Column(db.String(255), nullable=True)
    user_agent = db.Column(db.String(512), nullable=True)
    auth_type = db.Column(db.String(16), nullable=False)
    authenticated = db.Column(db.Boolean, nullable=False, default=False)
    user_id = db.Column(db.Integer, nullable=True, index=True)
    username = db.Column(db.String(128), nullable=True)
    apikey_id = db.Column(db.Integer, nullable=True, index=True)
    apikey_description = db.Column(db.String(255), nullable=True)
    request_body = db.Column(db.Text(), nullable=True)
    response_body = db.Column(db.Text(), nullable=True)

    def __repr__(self):
        return '<ApiHistory {0} {1} {2}>'.format(
            self.method, self.path, self.status_code)
