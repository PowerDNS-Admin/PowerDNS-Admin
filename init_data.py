#!/usr/bin/env python3

from app import app, db
from app.models import Role, Setting, DomainTemplate

admin_role = Role(name='Administrator', description='Administrator')
user_role = Role(name='User', description='User')

setting_1 = Setting(name='maintenance', value='False')
setting_2 = Setting(name='fullscreen_layout', value='True')
setting_3 = Setting(name='record_helper', value='True')
setting_4 = Setting(name='login_ldap_first', value='True')
setting_5 = Setting(name='default_record_table_size', value='15')
setting_6 = Setting(name='default_domain_table_size', value='10')
setting_7 = Setting(name='auto_ptr', value='False')

template_1 = DomainTemplate(name='basic_template_1', description='Basic Template #1')
template_2 = DomainTemplate(name='basic_template_2', description='Basic Template #2')
template_3 = DomainTemplate(name='basic_template_3', description='Basic Template #3')

db.session.add(admin_role)
db.session.add(user_role)

db.session.add(setting_1)
db.session.add(setting_2)
db.session.add(setting_3)
db.session.add(setting_4)
db.session.add(setting_5)
db.session.add(setting_6)
db.session.add(setting_7)

db.session.add(template_1)
db.session.add(template_2)
db.session.add(template_3)

db.session.commit()
