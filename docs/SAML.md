# SAML Authentication

SAML is a way to set up Single Sign-On authentication on PowerDNS-Admin.

To enable and configure SAML, login as an Administrator, navigate to Settings -> Authentication and select the SAML tab. The settings are categorized accordingly.

## General
* **Enable SAML**

## IDP
* **IDP Entity ID** - Specify the EntityID of the IDP to use.
Only needed if more the XML provided in the SAML_METADATA_URL contains more than 1 IDP Entity.

* **IDP Metadata URL** - Url where the XML of the Identity Provider Metadata is published.
* **IDP Metadata Cache Lifetime** - Cache Lifetime in minutes before fresh metadata are fetched from the IDP Metadata URL
**IDP SSO Binding** - SAML SSO binding format required for the IDP to use
**IDP SLO Binding** - SAML SLO binding format required for the IDP to use

**NOTE:** The Binding settings are currently *disabled*, as the underlying saml library currently supports only the Redirect binding for IDP endpoints.

## SP

**SP Entity ID** - Specify the EntityID of your Service Provider (SP).
**SP NameID Format** - NameID format to request. This specifies the content of the NameID and any associated processing rules.
**SP Metadata Cache** Duration - Set the cache duration of generated metadata.
Use PT5M to set cache duration to 5 minutes.
**SP Metadata Valid Until** - Set the expiration date, in XML DateTime String format, for generated metadata.
**XML DateTime String Format**: "YYYY-MM-DDThh:mm:ssZ", Z can be Z for timezone 0 or "+-hh:mm" for other timezones.
**Sign SP Metadata** - Choose whether metadata produced is signed.
**SP ACS Binding** - SAML Assertion Consumer Service Binding Format for the SP to use on login.
**SP SLS Binding** - SAML Single Logout Service Binding Format for the SP to use on logout.

**NOTE:** The Binding settings are currently disabled, as in the underlying saml library, the ACS endpoint currently supports only the HTTP-POST binding, while the SLS endpoint supports only HTTP-Redirect.

## SP ATTRIBUTES

**Requested Attributes** - The following parameter defines RequestedAttributes section in SAML metadata since certain IDPs require explicitly requesting attributes.
If not provided, the Attribute Consuming Service Section will not be available in metadata.

Possible attributes:

*name* (mandatory), *nameFormat*, *isRequired*, *friendlyName*

**NOTE:** This parameter requires to be entered in valid JSON format as displayed below and multiple attributes can be given. The following example:

``SAML_SP_REQUESTED_ATTRIBUTES = '[
{"name": "urn:oid:0.9.2342.19200300.100.1.3", "nameFormat": "urn:oasis:names:tc:SAML:2.0:attrname-format:uri", "isRequired": true, "friendlyName": "email"},
{"name": "mail", "isRequired": false, "friendlyName": "test-field"}
]'``

produces the following metadata section:

``<md:AttributeConsumingService index="1">
<md:RequestedAttribute Name="urn:oid:0.9.2342.19200300.100.1.3" NameFormat="urn:oasis:names:tc:SAML:2.0:attrname-format:uri" FriendlyName="email" isRequired="true"/>
<md:RequestedAttribute Name="mail" FriendlyName="test-field"/>
</md:AttributeConsumingService>``

* **Attributes** - The following attribute values **must** be derived from Requested Attributes, and **must** be in the form of a valid URN (e.g. *urn:oid:2.5.4.4*):
    - Email - Attribute to use for Email address.
    - Given Name - Attribute to use for Given name.
    - Surname - Attribute to use for Surname.
    - Username - Attribute to use for username.

* **SP Contact Attributes** - These may be generic strings containing your information:
    - SP Entity Name - Contact information about your SP, to be included in the generated metadata.
    - SP Entity Mail - Contact information about your SP, to be included in the generated metadata.

## ENCRYPTION

* The **Cert File** - **Cert Key** pair configures the path to certificate file and its respective private key file.
It is used for signing metadata, encrypting tokens and all other signing/encryption tasks during communication between IDP and SP.

**NOTE:** If these two parameters aren't explicitly provided, a self-signed certificate-key pair will be generated.

* **Sign Authentication Request** - Configures if the SP should sign outgoing authentication requests.
* **Sign Logout Request & Response** - Configures if the SP should sign outgoing Logout requests & Logout responses.
* **Want Assertions Encrypted** - Choose whether the SP expects incoming assertions received from the IDP to be encrypted.
* **Want Assertions Signed** - Choose whether the SP expects incoming assertions to be signed.
* **NameID Encrypted** - Indicates that the outgoing nameID of the logoutRequest sent by this SP will be encrypted.
* **Want NameID Encrypted** - Indicates a requirement for the incoming NameID received by this SP to be encrypted.
* **Want Message Signed** - Choose whether the SP expects incoming messages to be signed.
* **Digest Algorithm** - Encryption algorithm for the DigestValue, which is part of the validation process to ensure the integrity of the XML message.
* **Signature Algorithm** - Encryption algorithm for the message Signature.

## LOGOUT

* **SAML Logout** - Choose whether user is logged out of the SAML session using SLO.

If enabled, use SAML standard logout mechanism retreived from IDP metadata.

If disabled, don't care about SAML session on logout.
Logout from PowerDNS-Admin only and keep SAML session authenticated.
* **Logout URL** - Configure to redirect to a url different than PowerDNS-Admin login after a successful SAML logout.

## AUTOPROVISION
Assert user Admin status and associated Accounts with SAML Attributes.

* **Admin** - Attribute to get admin status from.

If set, look for the value 'true' to set a user as an administrator.

If not included in assertion, or set to something other than 'true', the user is set as a non-administrator user.
* **Account** - Attribute to get account names from.

If set, the user will be added and removed from accounts to match what's in the login assertion.

Accounts that don't exist will be created and the user added to them.