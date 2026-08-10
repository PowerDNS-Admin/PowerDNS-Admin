### OAuth Authentication

#### Microsoft Entra ID

To use Microsoft Entra ID for authentication, register PowerDNS-Admin in the Microsoft Entra admin center. This requires your PowerDNS-Admin web interface to use an HTTPS URL.

* In Microsoft Entra ID, select App registrations and create a new one. Give it any name you want. The redirect URI should use the Web platform and the format `https://powerdnsadmin/azure/authorized` (replace the host name appropriately). The legacy `/azure/` route remains unchanged for compatibility.
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

#### Keycloak

To link to Keycloak for authentication, you need to create a new client in the Keycloak Administration Console. 
* Log in to the Keycloak Administration Console
* Go to Clients > Create
* Enter a Client ID (for example 'powerdns-admin') and click 'Save'
* Scroll down to 'Access Type' and choose 'Confidential'.
* Scroll down to 'Valid Redirect URIs' and enter 'https://<pdnsa address>/oidc/authorized'
* Click 'Save'
* Go to the 'Credentials' tab and copy the Client Secret
* Log in to PowerDNS-Admin and go to 'Settings > Authentication > OpenID Connect OAuth'
* Enter the following details:
  * Client key -> Client ID
  * Client secret > Client secret copied from keycloak
  * Scope: `openid profile email`
  * API URL: https://<keycloak url>/auth/realms/<realm>/protocol/openid-connect/
  * Token URL: https://<keycloak url>/auth/realms/<realm>/protocol/openid-connect/token
  * Authorize URL: https://<keycloak url>/auth/realms/<realm>/protocol/openid-connect/auth
  * Logout URL: https://<keycloak url>/auth/realms/<realm>/protocol/openid-connect/logout
  * Leave the rest default
* Save the changes and restart PowerDNS-Admin
* Use the new 'Sign in using OpenID Connect' button to log in.

#### OpenID Connect OAuth
To link to oidc service for authenticationregister your PowerDNS-Admin in the OIDC Provider. This requires your PowerDNS-Admin web interface to use an HTTPS URL.

Enable OpenID Connect OAuth option.
* Client key, The client ID
* Scope, The scope of the data. The required `openid` scope is added automatically.
* API URL, <oidc_provider_link>/auth (The ending can be different with each provider)
* Token URL, <oidc_provider_link>/token 
* Authorize URL, <oidc_provider_link>/auth
* Metadata URL, <oidc_provider_link>/.well-known/openid-configuration
* Logout URL fallback, <oidc_provider_link>/logout. This is optional when the
  provider metadata publishes `end_session_endpoint`.

PowerDNS-Admin implements
[OpenID Connect RP-Initiated Logout 1.0](https://openid.net/specs/openid-connect-rpinitiated-1_0.html).
At logout it prefers the discovered `end_session_endpoint`, sends the login ID
token as `id_token_hint`, identifies the configured client with `client_id`,
and sends the registered login URL as `post_logout_redirect_uri`. If discovery
does not publish a logout endpoint, the configured Logout URL fallback is
used. If neither is available, only the local PowerDNS-Admin session is ended.
Register the PowerDNS-Admin login URL as an allowed post-logout redirect URI at
the provider.

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
