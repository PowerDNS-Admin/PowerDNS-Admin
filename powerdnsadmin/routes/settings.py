import json
from flask import Blueprint, render_template, request
from flask_login import login_required
from ..decorators import admin_role_required
from ..models.setting import Setting

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
    from powerdnsadmin.lib.settings import AppSettings
    result = {'status': 1, 'messages': [], 'data': {}}

    if request.form.get('commit') == '1':
        model = Setting()
        data = json.loads(request.form.get('data'))

        for key, value in data.items():
            if key in AppSettings.defaults:
                model.set(key, value)

    result['data'] = Setting().get_all()

    return result
