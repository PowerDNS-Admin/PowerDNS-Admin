from flask import current_app, session
from flask_login import current_user
from .base import db


class Sessions(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(255), index=True, unique=True)
    data = db.Column(db.BLOB)
    expiry = db.Column(db.DateTime)

    def __init__(self,
                 id=None,
                 session_id=None,
                 data=None,
                 expiry=None):
        self.id = id
        self.session_id = session_id
        self.data = data
        self.expiry = expiry

    def __repr__(self):
        return '<Sessions {0}>'.format(self.id)

    @staticmethod
    def clean_up_expired_sessions():
        """Clean up expired sessions in the database"""
        from datetime import datetime
        from sqlalchemy import or_
        from sqlalchemy.exc import SQLAlchemyError

        try:
            db.session.query(Sessions).filter(or_(Sessions.expiry < datetime.now(), Sessions.expiry is None)).delete()
            db.session.commit()
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(e)
            return False
        return True
