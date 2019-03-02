#!/usr/bin/env python3

from app import db
from app.models import Role, DomainTemplate

admin_role = Role(name="Administrator", description="Administrator")
user_role = Role(name="User", description="User")

template_1 = DomainTemplate(name="basic_template_1", description="Basic Template #1")
template_2 = DomainTemplate(name="basic_template_2", description="Basic Template #2")
template_3 = DomainTemplate(name="basic_template_3", description="Basic Template #3")

db.session.add(admin_role)
db.session.add(user_role)

db.session.add(template_1)
db.session.add(template_2)
db.session.add(template_3)

db.session.commit()
