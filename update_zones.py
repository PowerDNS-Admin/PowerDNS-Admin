#!/usr/bin/env python3

####################################################################################################################################
# A CLI Script to update list of domains instead from the UI. Can be useful for people who want to execute updates from a cronjob
#
# Tip:
# When running from a cron, use flock (you might need to install it) to be sure only one process is running a time. eg:
# */5 * * * * flock -xn "/tmp/pdns-update-zones.lock" python /var/www/html/apps/poweradmin/update_zones.py >/dev/null 2>&1
#
##############################################################

### Imports
import sys
import logging

from powerdnsadmin import create_app
from powerdnsadmin.models.domain import Domain
from powerdnsadmin.models.setting import Setting

app = create_app()
app.logger.setLevel(logging.INFO)

with app.app_context():
    status = Setting().get('bg_domain_updates')

    ### Check if bg_domain_updates is set to true
    if not status:
        app.logger.error('Please turn on "bg_domain_updates" setting to run this job.')
        sys.exit(1)

    ### Start the update process
    app.logger.info('Update zones from nameserver API')

    d = Domain().update()
