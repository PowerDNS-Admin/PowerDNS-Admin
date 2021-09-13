Larger organisations often have many active applications such as PowerDns-Admin. Therefore, occasionally the need arises for there to be an access management mechanism that monitors every application available, especially concerning the role management aspect on each application.

Powerdns-admin already provides a mechanism for a finer grained control of users'  privileges by using LDAP static groups, which is configurable with the set of options under the "Group Security". However, while static groups are widely known and available on the majority of the ldap deployments, nowadays are considered administratively inflexible. A workaround to static groups limitations is offered by more recent versions of OpenLDAP servers(openldap 2.5.x) via dynamic groups.

However recent designs tend to implement access management based on ldap attributes with URN syntax values that reside on the user's object and encompass into their structure all service specific membership scenarios, otherwise referred to as autoprovisioning using URN values.
With our proposed feature, we do implement autoprovisioning using URN values utilizing an attribute passed in the user's LDAP Object. The allowed syntax for records inside this attribute is:

```text
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

In order to keep users' privileges in-sync between the PDA's database and the ldap,  when no valid "powerdns-admin" values are found for the logged-in user, PDA will purge all privileges from the local database for this user. To avoid unintentional wipe outs of existing PDA privileges especially when admins enable this feature for the first time, also available in the proposed feature is the option "Purge Roles if empty". If toggled on, ldap entries that have no valid "powerdns-admin" records to their object's attribute, will lose all their associations with any domain or account, also reverting to a PDA-User in the process, despite their current role in the local db. If toggled off, in the same scenario they get to keep their existing associations and their current PDA-Role. 

How to configure:
1) Login as an admin to PowerDNS Admin.
2) Go to Settings --> Authentication.
3) Under Authentication, select LDAP.
4) Disable Group Security, if enabled.
5) Click the Radio Button for Role Autoprovisioning.
6) Fill in the required info -

* Role Provisioning field - your_LDAP_Field.
* Urn prefix - your_URN_Prefix.

7) Enable Purge Roles If Empty, if you so wish, and click confirm when the prompt appears.
8) Click Save.

<a href="https://ibb.co/rtRnXF5"><img src="https://i.ibb.co/vB62MVL/image.png" alt="image" border="0"></a>


Last but not least, provisioning PDA user privileges using urn values is a feature that can also be achieved while deploying other release mechanisms that PowerDns-Admin already supports, such as OpenID Connect. For these authentication providers there will occur a patch later down the line implementing the proposed feature to their standards/specifications.

