import json
from flask import Blueprint, render_template, request, Response
from flask_login import login_required
from ..decorators import admin_role_required

settings_bp = Blueprint('settings',
                        __name__,
                        template_folder='templates',
                        url_prefix='/settings')


@settings_bp.route('/', methods=['GET', 'POST'])
@login_required
@admin_role_required
def editor():
    return render_template('settings/editor.html')


@settings_bp.route('/api', methods=['POST'])
@login_required
@admin_role_required
def api():
    import jsonpickle
    from powerdnsadmin.lib.settings import Settings
    result = {'status': 1, 'messages': [], 'payload': {}}

    if request.form.get('commit') == '1':
        data = json.loads(request.form.get('data'))

        for name, value in data.items():
            setting = Settings.instance().get(name)
            setting.value = value
            setting.save()

    result['payload'] = {
        'legacy': Settings.instance().all(flatten=True),
        'settings': Settings.instance().all(),
    }

    return Response(jsonpickle.encode(result), mimetype='application/json')
