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

#### OpenID Connect OAuth
To link to oidc service for authenticationregister your PowerDNS-Admin in the OIDC Provider. This requires your PowerDNS-Admin web interface to use an HTTPS URL.

Enable OpenID Connect OAuth option.
* Client key, The client ID
* Scope, The scope of the data.
* API URL, <oidc_provider_link>/auth (The ending can be different with each provider)
* Token URL, <oidc_provider_link>/token 
* Authorize URL, <oidc_provider_link>/auth
* Logout URL, <oidc_provider_link>/logout

* Username, This will be the claim that will be used as the username. (Usually preferred_username)
* First Name, This will be the firstname of the user. (Usually given_name)
* Last Name, This will be the lastname of the user. (Usually family_name)
* Email, This will be the email of the user. (Usually email)

#### To create accounts on oidc login use the following properties:
* Autoprovision Account Name Property, This property will set the name of the created account.
  This property can be a string or a list.
* Autoprovision Account Description Property, This property will set the description of the created account.
  This property can be a string or a list.

If we get a variable named "groups" and "groups_description" from our IdP.
This variable contains groups that the user is a part of.
We will put the variable name "groups" in the "Name Property" and "groups_description" in the "Description Property".
This will result in the following account being created:
Input we get from the Idp:

```
{
	"preferred_username": "example_username",
	"given_name": "example_firstame",
	"family_name": "example_lastname",
	"email": "example_email",
	"groups": ["github", "gitlab"]
	"groups_description": ["github.com", "gitlab.com"]
}
```

The user properties will be:
```
Username: customer_username
First Name: customer_firstame
Last Name: customer_lastname
Email: customer_email
Role: User
```

The groups properties will be:
```
Name: github Description: github.com Members: example_username
Name: gitlab Description: gitlab.com Members: example_username
```	

If the option "delete_sso_accounts" is turned on the user will only be apart of groups the IdP provided and removed from all other accoubnts.
