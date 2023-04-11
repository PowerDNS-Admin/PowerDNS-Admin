Active Directory Setup - Tested with Windows Server 2012

1) Login as an admin to PowerDNS Admin

2) Go to Settings --> Authentication 

3) Under Authentication, select LDAP

4) Click the Radio Button for Active Directory

5) Fill in the required info -

* LDAP URI - ldap://ip.of.your.domain.controller:389
* LDAP Base DN - dc=yourdomain,dc=com
* Active Directory domain - yourdomain.com
* Basic filter - (objectCategory=person)
  * the brackets here are **very important**
* Username field - sAMAccountName
* GROUP SECURITY - Status - On
* Admin group - CN=Your_AD_Admin_Group,OU=Your_AD_OU,DC=yourdomain,DC=com
* Operator group - CN=Your_AD_Operator_Group,OU=Your_AD_OU,DC=yourdomain,DC=com
* User group - CN=Your_AD_User_Group,OU=Your_AD_OU,DC=yourdomain,DC=com

6) Click Save

7) Logout and re-login as an LDAP user from each of the above groups.

If you're having problems getting the correct information for your groups, the following tool can be useful -

https://docs.microsoft.com/en-us/sysinternals/downloads/adexplorer

In our testing, groups with spaces in the name did not work, we had to create groups with underscores to get everything operational. 

YMMV
