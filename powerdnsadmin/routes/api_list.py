from flask import Blueprint

apilist_bp = Blueprint('apilist', __name__, url_prefix='/api')

@apilist_bp.route('/', methods=['GET'])
def index():
    return '[{"url": "/api/v1", "version": 1}]', 200
