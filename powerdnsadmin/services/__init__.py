from .base import authlib_oauth_client

def init_app(app):
    authlib_oauth_client.init_app(app)