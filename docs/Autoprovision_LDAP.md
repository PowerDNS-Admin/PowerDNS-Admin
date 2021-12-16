# Configure PDA user privileges based on LDAP Attributes

Provisioning the roles and the associations of a user based on an attribute in his object, is a very useful practice for a variety of reasons, and can be implemented across multiple authentication providers for PDA. Below we demonstrate how to enable and configure Roles&Associations Provisioning during LDAP authentication.

The allowed syntax for records inside the attribute of the user's object is:

```text.
if PDA-Role∈[Administrator, Operator]:
    syntax:=prefix:"powerdns-admin":PDA-Role
else:
    syntax:=prefix:"powerdns-admin":PDA-Role:<domain>:<account>

where prefix is given by an admin of PDA in the configurable field "ADVANCE:Urn prefix".

i.e. some valid urn values could be:
urn:yourNID:yourOrganization:powerdns-admin:Administrator
urn:yourNID:yourOrganization:powerdns-admin:User:example.com            (supposing there is a domain in the local db called "example.com")
urn:yourNID:yourOrganization:powerdns-admin:User:example.com:examplenet (supposing there is an account in the local db called "examplenet")
urn:yourNID:yourOrganization:powerdns-admin:User::examplenet 
```
Note: To use Roles&Associations Provisioning in its fullest potential, the domains and the accounts provided in the entries must already exist, or else entries with no match in the local db will be skipped.

In order to keep users' privileges in-sync between the PDA's database and the LDAP,  when no valid "powerdns-admin" values are found for the logged-in user, PDA will purge all privileges from the local database for this user. To avoid unintentional wipe outs of existing PDA privileges especially when admins enable this feature for the first time, the option "Purge Roles if empty" is also available. If toggled on, LDAP/OIDC entries that have no valid "powerdns-admin" records to their object's attribute, will lose all their associations with any domain or account, also reverting to a PDA-User in the process, despite their current role in the local db. If toggled off, in the same scenario they get to keep their existing associations and their current PDA-Role. 

How to configure LDAP Roles Autoprovisioning:
1) Login as an admin to PowerDNS Admin.
2) Go to Settings --> Authentication.
3) Under Authentication, select LDAP.
4) Disable Group Security, if enabled.
5) Click the Radio Button for Roles Autoprovisioning.
6) Fill in the required info:

* Role Provisioning field - your_LDAP_Field.
* Urn prefix - your_URN_Prefix.

7) Enable Purge Roles If Empty, if you so wish, and click confirm when the prompt appears.
8) Click Save.

<a href="https://ibb.co/189yxmB"><img src="https://i.ibb.co/yW8vJQK/Screenshot-2021-09-13-at-13-39-33-Authentication-Settings-Power-DNS-Admin.png" alt="Screenshot-Authentication-Settings-Power-DNS-Admin" border="0"></a>