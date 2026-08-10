import os
import json
import traceback
from yaml import Loader, load
from flask import Blueprint, make_response, current_app, abort

swagger_bp = Blueprint('swagger',
                       __name__,
                       template_folder='templates',
                       url_prefix='/')


@swagger_bp.route('/swagger', methods=['GET'])
def swagger_spec():
    try:
        spec_path = os.path.join(current_app.root_path, "swagger-spec.yaml")
        spec = open(spec_path, 'r')
        loaded_spec = load(spec.read(), Loader)
    except Exception as e:
        current_app.logger.error(
            'Cannot view swagger spec. Error: {0}'.format(e))
        current_app.logger.debug(traceback.format_exc())
        abort(500)

    resp = make_response(json.dumps(loaded_spec), 200)
    resp.headers['Content-Type'] = 'application/json'

    return resp
