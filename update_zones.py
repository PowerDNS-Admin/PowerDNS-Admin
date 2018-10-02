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
from app.models import Domain
from config import BG_DOMAIN_UPDATES

import sys
import logging as logger

### Define logging
logging = logger.getLogger(__name__)

### Check if BG_DOMAIN_UPDATES is set to true
if not BG_DOMAIN_UPDATES:
  logging.error('Set BG_DOMAIN_UPDATES to True in config.py')
  sys.exit(1)

### Start the update process
logging.info('Update zones from nameserver API')

d = Domain().update()
