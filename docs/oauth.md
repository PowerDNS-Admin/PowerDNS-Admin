### OAuth Authentication

#### Microsoft Azure

To link to Azure for authentication, you need to register PowerDNS-Admin in Azure.  This requires your PowerDNS-Admin web interface to use an HTTPS URL.

* Under the Azure Active Directory, select App Registrations, and create a new one.  Give it any name you want, and the Redirect URI shoule be type 'Web' and of the format https://powerdnsadmin/azure/authorized (replace the host name approriately).
* Select the newly-created registration
* On the Overview page, the Application ID is your new Client ID to use with PowerDNS-Admin
* On the Overview page, make a note of your Directory/Tenant ID - you need it for the API URLs later
* Ensure Access Tokens are enabled in the Authentication section
* Under Certificates and Secrets, create a new Client Secret.  Note this secret as it is the new Client Secret to use with PowerDNS-Admin
* Under API Permissions, you need to add permissions.  Add permissions for Graph API, Delegated.  Add email, openid, profile, User.Read and possibly User.Read.All.  You then need to grant admin approval for your organisation.

Now you can enable the OAuth in PowerDNS-Admin.
* For the Scope, use 'User.Read openid mail profile'
* Replace the [tenantID] in the default URLs for authorize and token with your Tenant ID.
* Restart PowerDNS-Admin

This should allow you to log in using OAuth.