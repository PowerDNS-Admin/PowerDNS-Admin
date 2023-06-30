#!/bin/bash

# Create a new group for PowerDNS-Admin
groupadd powerdnsadmin

# Create a user for PowerDNS-Admin
useradd --system -g powerdnsadmin powerdnsadmin

# Make the new user and group the owners of the PowerDNS-Admin files
chown -R powerdnsadmin:powerdnsadmin /opt/web/powerdns-admin

# Start the PowerDNS-Admin service
systemctl start powerdns-admin

# Enable the PowerDNS-Admin service to start automatically at boot
systemctl enable powerdns-admin
