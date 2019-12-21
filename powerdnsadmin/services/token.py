from flask import current_app
from itsdangerous import URLSafeTimedSerializer


def generate_confirmation_token(email):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return serializer.dumps(email, salt=current_app.config['SALT'])


def confirm_token(token, expiration=86400):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = serializer.loads(token,
                                 salt=current_app.config['SALT'],
                                 max_age=expiration)
    except Exception as e:
        current_app.logger.debug(e)
        return False
    return email
