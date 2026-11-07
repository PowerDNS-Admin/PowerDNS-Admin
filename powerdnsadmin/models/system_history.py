from datetime import datetime

from .base import db


class SystemHistory(db.Model):
    """One row for each change to an application setting.

    user_id is a copy taken at change time, not a foreign key, so deleting
    the account leaves the row. Credential values are stored as
    ``[redacted]``.
    """

    __tablename__ = 'system_history'

    id = db.Column(db.Integer, primary_key=True)
    created_on = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    setting_name = db.Column(db.String(64), nullable=False, index=True)
    old_value = db.Column(db.Text(), nullable=True)
    new_value = db.Column(db.Text(), nullable=True)
    username = db.Column(db.String(128), nullable=True)
    user_id = db.Column(db.Integer, nullable=True, index=True)
    remote_addr = db.Column(db.String(255), nullable=True)

    def __repr__(self):
        return '<SystemHistory {0}>'.format(self.setting_name)
