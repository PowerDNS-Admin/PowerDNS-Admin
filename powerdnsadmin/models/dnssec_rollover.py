import json
from datetime import datetime

from .base import db


class DnssecRollover(db.Model):
    """Persist the safe, guided portion of a DNSSEC key rollover."""

    __tablename__ = 'dnssec_rollover'

    id = db.Column(db.Integer, primary_key=True)
    domain_id = db.Column(
        db.Integer, db.ForeignKey('domain.id', ondelete='CASCADE'),
        nullable=False, index=True)
    rollover_type = db.Column(db.String(16), nullable=False)
    keytype = db.Column(db.String(8), nullable=False)
    state = db.Column(db.String(32), nullable=False, index=True)
    old_key_ids = db.Column(db.Text(), nullable=False, default='[]')
    new_key_ids = db.Column(db.Text(), nullable=False, default='[]')
    algorithm = db.Column(db.String(32), nullable=False)
    bits = db.Column(db.Integer, nullable=False)
    started_by = db.Column(db.String(128), nullable=False)
    started_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    not_before = db.Column(db.DateTime, nullable=True)
    parent_ds_confirmed_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    error = db.Column(db.Text(), nullable=True)
    active = db.Column(db.Boolean, nullable=False, default=True, index=True)
    key_references = db.relationship(
        'DnssecRolloverKey',
        back_populates='rollover',
        cascade='all, delete-orphan',
        order_by='DnssecRolloverKey.id',
    )

    @staticmethod
    def _loads_key_ids(value):
        try:
            return [int(key_id) for key_id in json.loads(value or '[]')]
        except (TypeError, ValueError, json.JSONDecodeError):
            return []

    @property
    def old_keys(self):
        return self._loads_key_ids(self.old_key_ids)

    @old_keys.setter
    def old_keys(self, value):
        self.old_key_ids = json.dumps([int(key_id) for key_id in value])

    @property
    def new_keys(self):
        return self._loads_key_ids(self.new_key_ids)

    @new_keys.setter
    def new_keys(self, value):
        self.new_key_ids = json.dumps([int(key_id) for key_id in value])

    def to_dict(self):
        old_references = [
            reference for reference in self.key_references
            if reference.role == 'old'
        ]
        new_references = [
            reference for reference in self.key_references
            if reference.role == 'new'
        ]
        return {
            'id': self.id,
            'type': self.rollover_type,
            'keyType': self.keytype,
            'state': self.state,
            'oldKeyIds': (
                [reference.backend_key_id for reference in old_references]
                if old_references else self.old_keys),
            'newKeyIds': (
                [reference.backend_key_id for reference in new_references]
                if new_references else self.new_keys),
            'keyReferences': [
                reference.to_dict() for reference in self.key_references
            ],
            'algorithm': self.algorithm,
            'bits': self.bits,
            'startedBy': self.started_by,
            'startedAt': (
                self.started_at.isoformat() if self.started_at else None),
            'notBefore': (
                self.not_before.isoformat() if self.not_before else None),
            'parentDsConfirmedAt': (
                self.parent_ds_confirmed_at.isoformat()
                if self.parent_ds_confirmed_at else None),
            'completedAt': (
                self.completed_at.isoformat() if self.completed_at else None),
            'error': self.error,
            'active': self.active,
        }


class DnssecRolloverKey(db.Model):
    """Stable public identity for a PowerDNS cryptokey in a rollover."""

    __tablename__ = 'dnssec_rollover_key'
    __table_args__ = (
        db.UniqueConstraint(
            'rollover_id', 'role', 'fingerprint',
            name='uq_dnssec_rollover_key_identity'),
    )

    id = db.Column(db.Integer, primary_key=True)
    rollover_id = db.Column(
        db.Integer,
        db.ForeignKey('dnssec_rollover.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    role = db.Column(db.String(8), nullable=False)
    backend_key_id = db.Column(db.Integer, nullable=True, index=True)
    fingerprint = db.Column(db.String(64), nullable=False, index=True)
    key_tag = db.Column(db.Integer, nullable=False)
    keytype = db.Column(db.String(8), nullable=False)
    algorithm = db.Column(db.String(32), nullable=False)
    bits = db.Column(db.Integer, nullable=True)
    dnskey = db.Column(db.Text(), nullable=False)
    ds = db.Column(db.Text(), nullable=False, default='[]')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    rollover = db.relationship(
        'DnssecRollover', back_populates='key_references')

    @property
    def ds_records(self):
        try:
            return list(json.loads(self.ds or '[]'))
        except (TypeError, ValueError, json.JSONDecodeError):
            return []

    @ds_records.setter
    def ds_records(self, value):
        self.ds = json.dumps(list(value or []))

    @classmethod
    def from_identity(cls, rollover, role, identity):
        reference = cls(
            rollover=rollover,
            role=role,
            backend_key_id=identity['backendKeyId'],
            fingerprint=identity['fingerprint'],
            key_tag=identity['keyTag'],
            keytype=identity['keyType'],
            algorithm=identity['algorithm'],
            bits=identity['bits'],
            dnskey=identity['dnskey'],
        )
        reference.ds_records = identity['ds']
        return reference

    def to_dict(self):
        return {
            'role': self.role,
            'backendKeyId': self.backend_key_id,
            'fingerprint': self.fingerprint,
            'keyTag': self.key_tag,
            'keyType': self.keytype,
            'algorithm': self.algorithm,
            'bits': self.bits,
            'dnskey': self.dnskey,
            'ds': self.ds_records,
        }
