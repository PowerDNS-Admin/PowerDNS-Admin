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
To link to oidc service for authentication you will need to register your PowerDNS-Admin in the OIDC Provider.
This means you will need to have a client key, client secret a redirect URI that is registered.

After you have talked to your oidc provider or created it yourself you will need to enter the following credits:
Make sure you Enable OpenID Connect OAuth option.
* Client key, This will be your client ID and essentially your "authentication" against the IdP.
* Client secret, Essentially a password to your user.
* Scope, The scope of the userinfo data you get.
* API URL, <oidc_provider>/auth (Each one will be different but usually this is the standard)
* Token URL, <oidc_provider>/token 
* Authorize URL, <oidc_provider>/auth
* Logout URL, <oidc_provider>/logout

* Username, This will be the claim that will be used as the username. (Usually preferred_username)
* First Name, This will be the firstname of the user. (Usually given_name)
* Last Name, This will be the lastname of the user. (Usually family_name)
* Email, This will be the email of the user. (Usually email)

#### To create accounts on oidc login we will need to use the following properties:
* Autoprovision Account Name Property, This property will set the name of the created account.
  This property can be either a string or a list.
* Autoprovision Account Description Property, This property will set the description of the created account.
  This property can also be either a string or a list.

Let's say we get a variable named "groups" from our IdP.
This variable contains groups that the user is a part from.
We will put the variable name "groups" in both properties and it will result in the following account:
Example:
Input we get from the Idp:

```
{
	"preferred_username": "customer_username",
	"given_name": "customer_firstame",
	"family_name": "customer_lastname",
	"email": "customer_email",
	"groups": ["github", "gitlab"]
}
```

The user created will be:
```
Username: customer_username
First Name: customer_firstame
Last Name: customer_lastname
Email: customer_email
Role: User
```

The groups created will be:
```
Name: github Description: github Members: customer_username
Name: gitlab Description: gitlab Members: customer_username
```	

If the user gets removed from one of the groups he will also get removed from that group account.
