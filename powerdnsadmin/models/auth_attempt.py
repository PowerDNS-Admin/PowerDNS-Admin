"""Shared pre-authentication counters.

One row per source address, account name, or source-and-account pair.
The values are failure counts and lock times, never passwords.
"""
from datetime import datetime

from .base import db


class AuthAttempt(db.Model):
    __tablename__ = 'auth_attempt'
    __table_args__ = (
        db.UniqueConstraint(
            'scope', 'subject', name='uix_auth_attempt_scope_subject'),
    )

    id = db.Column(db.Integer, primary_key=True)
    scope = db.Column(db.String(16), nullable=False)
    subject = db.Column(db.String(160), nullable=False)
    failures = db.Column(
        db.Integer, nullable=False, default=0, server_default='0')
    lockouts = db.Column(
        db.Integer, nullable=False, default=0, server_default='0')
    window_started = db.Column(db.DateTime, nullable=True)
    locked_until = db.Column(db.DateTime, nullable=True)
    seen_values = db.Column(db.Text(), nullable=True)
    updated_at = db.Column(db.DateTime, nullable=True, index=True,
                           default=datetime.utcnow)
