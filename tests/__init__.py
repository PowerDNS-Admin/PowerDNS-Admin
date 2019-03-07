from powerdns_admin.app import app

ctx = app.app_context()
ctx.push()
