# Migrate SAML Configuration from config files to Settings

The latest PowerDNS-Admin version introduces a User Interface for configuring SAML Authentication. This guide helps you migrate your existing SAML configuration, from the config files to the UI.

Before upgrading, **SAVE your *configs/development.py* OR *configs/production.py*** files, because you will need to remember your SAML settings in order to pass them in the UI interface

As an *Administrator*, navigate to Settings->Authentication and select the **SAML** tab. There, copy these config settings to the new fields, following this example:

> **PREVIOUS_CONFIG_SETTING**: *Category* -> New Setting Name

The settings are sorted in the order of the previous config settings.

* **SAML_ENABLED**: General->Enable SAML

If SAML_ENABLED was False and you do not need the SAML feature, you are not required to change any settings.

* **SAML_METADATA_URL**: *IDP* -> IDP Metadata URL
* **SAML_METADATA_CACHE_LIFETIME**-> *IDP* Metadata Cache Lifetime (in minutes)
* **SAML_IDP_SSO_BINDING**: *IDP* -> IDP SSO Binding

IDP SSO Binding is disabled, as the underlying SAML library currently supports only the Redirect binding for IDP endpoints.

* **SAML_IDP_ENTITY_ID**: *IDP* -> IDP Entity ID
* **SAML_NAMEID_FORMAT**: *SP* -> SP NameID Format

* **SAML_SP_REQUESTED_ATTRIBUTES**: *SP ATTRIBUTES* -> Requested Attributes

Copy the entire block of attributes in the text box, **in a single line, *without* backslashes**.

* **SAML_ATTRIBUTE_EMAIL**: *SP ATTRIBUTES* -> Email
* **SAML_ATTRIBUTE_GIVENNAME**: *SP ATTRIBUTES* -> Given Name
* **SAML_ATTRIBUTE_SURNAME**: *SP ATTRIBUTES* -> Surname
* **SAML_ATTRIBUTE_USERNAME**: *SP ATTRIBUTES* -> Username

* **SAML_ATTRIBUTE_ADMIN**: *AUTOPROVISION* -> Admin SP Attribute
* **SAML_ATTRIBUTE_ACCOUNT**: *AUTOPROVISION* -> Account SP Attribute

* **SAML_SP_ENTITY_ID**: *SP* -> SP Entity ID
* **SAML_SP_CONTACT_NAME**: *SP ATTRIBUTES* -> SP Contact Name
* **SAML_SP_CONTACT_MAIL**: *SP ATTRIBUTES* -> SP Contact Mail

* **SAML_CERT_FILE**: *SIGNING & ENCRYPTION* -> Cert File
* **SAML_CERT_KEY**: *SIGNING & ENCRYPTION* -> Cert Key

* **SAML_SIGN_REQUEST**: *SIGNING & ENCRYPTION* -> Sign Authentication Request, Sign Logout Request & Response

Both the above settings were handled by SAML_SIGN_REQUEST previously.

* **SAML_LOGOUT**: *LOGOUT* -> SAML Logout
* **SAML_LOGOUT_URL**: *LOGOUT* -> Logout URL

* **SAML_ASSERTION_ENCRYPTED**: *SIGNING & ENCRYPTION* -> Want Assertions Encrypted