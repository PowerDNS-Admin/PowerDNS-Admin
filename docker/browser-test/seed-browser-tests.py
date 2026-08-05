"""Seed the disposable database used by the Docker browser-test profile."""

import os

import requests

from powerdnsadmin import create_app
from powerdnsadmin.models.base import db
from powerdnsadmin.models.setting import Setting
from powerdnsadmin.models.user import User


def main():
    app = create_app()
    with app.app_context():
        pdns_url = "{0}://{1}:{2}".format(
            os.environ.get("PDNS_PROTO", "http"),
            os.environ.get("PDNS_HOST", "pdns-server-browser"),
            os.environ.get("PDNS_PORT", "8081"),
        )

        settings = {
            "pdns_api_url": pdns_url,
            "pdns_api_key": os.environ.get("PDNS_API_KEY", "changeme"),
            "local_db_enabled": True,
            "signup_enabled": False,
            "captcha_enable": False,
            "allow_user_create_domain": True,
            "allow_user_remove_domain": True,
            "warn_session_timeout": False,
            "record_helper": True,
            "bg_domain_updates": False,
        }
        for name, value in settings.items():
            if not Setting().set(name, value):
                raise RuntimeError("Could not seed setting: {0}".format(name))

        # A stored URL is not enough: fail startup unless the configured
        # application settings can authenticate to the composed PDNS API.
        configured_url = Setting().get("pdns_api_url")
        configured_key = Setting().get("pdns_api_key")
        if configured_url != pdns_url or configured_key != settings["pdns_api_key"]:
            raise RuntimeError("Persisted PowerDNS settings do not match the test environment")
        response = requests.get(
            "{0}/api/v1/servers/localhost".format(configured_url.rstrip("/")),
            headers={"X-API-Key": configured_key},
            timeout=5,
        )
        response.raise_for_status()
        if response.json().get("id") != "localhost":
            raise RuntimeError("Unexpected PowerDNS server response")

        username = os.environ.get("BROWSER_TEST_USERNAME", "browser-admin")
        if User.query.filter_by(username=username).first() is None:
            user = User(
                username=username,
                plain_text_password=os.environ.get(
                    "BROWSER_TEST_PASSWORD", "BrowserTest123!"
                ),
                firstname="Browser",
                lastname="Test",
                email="browser-tests@example.invalid",
            )
            result = user.create_local_user()
            if not result["status"]:
                raise RuntimeError(result["msg"])

        db.session.remove()


if __name__ == "__main__":
    main()
