import os
import tempfile
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from flask import Flask
from sqlalchemy import event

import powerdnsadmin.models  # noqa: F401  (register every model before create_all)
from powerdnsadmin.lib.password_login import register_otp_failure
from powerdnsadmin.models.base import db
from powerdnsadmin.models.user import User


def _enable_wal(dbapi_connection, _connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute('PRAGMA journal_mode=WAL')
    cursor.execute('PRAGMA busy_timeout=30000')
    cursor.close()


def _sqlite_app(path):
    app = Flask('otp-sqlite-concurrency')
    app.config.update(
        SQLALCHEMY_DATABASE_URI='sqlite:///' + path,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SQLALCHEMY_ENGINE_OPTIONS={
            'connect_args': {'timeout': 30},
        },
        SECRET_KEY='sqlite-otp-concurrency',
    )
    db.init_app(app)
    with app.app_context():
        event.listen(db.engine, 'connect', _enable_wal)
        db.engine.dispose()
    return app


def test_concurrent_otp_failures_lock_the_account_on_sqlite():
    handle, path = tempfile.mkstemp(suffix='.sqlite')
    os.close(handle)
    app = _sqlite_app(path)
    try:
        with app.app_context():
            db.engine.dispose()
            db.create_all()
            account = User(
                username='sqlite-lock',
                email='lock@example.com',
                reload_info=False,
            )
            account.password = 'not-used'
            account.otp_failed_attempts = 0
            account.otp_lockouts = 0
            account.confirmed = 1
            account.session_version = 0
            db.session.add(account)
            db.session.commit()
            user_id = account.id

        barrier = Barrier(5)

        def fail_once(_slot):
            with app.app_context():
                try:
                    account = db.session.get(User, user_id)
                    barrier.wait(timeout=10)
                    register_otp_failure(account)
                finally:
                    db.session.remove()

        with ThreadPoolExecutor(max_workers=5) as pool:
            list(pool.map(fail_once, range(5)))

        with app.app_context():
            account = db.session.get(User, user_id)
            assert account.otp_failed_attempts == 5
            assert account.otp_lockouts == 1
            assert account.otp_locked_until is not None
    finally:
        with app.app_context():
            db.session.remove()
            db.engine.dispose()
        for suffix in ('', '-wal', '-shm'):
            candidate = path + suffix
            if os.path.exists(candidate):
                os.unlink(candidate)
