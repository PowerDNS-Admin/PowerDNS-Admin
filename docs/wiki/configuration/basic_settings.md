### PowerDNSAdmin basic settings

PowerDNSAdmin has many features and settings available to be turned either off or on.
In this docs those settings will be explain.
To find the settings in the the dashboard go to settings>basic.

allow_user_create_domain: Allows the `User` role to create new zones through the GUI and API, including automation with User-role API keys. Disabled by default; Administrators and Operators can create zones regardless of this setting.

When enabled, new zone names may be unrelated to the user's or API key's existing zone and account assignments. Those assignments control access to existing zones, not the namespace for new zones. A key assigned to one zone can therefore create a separate, unrelated zone. This is expected self-service provisioning behavior. Backend validation and the optional `deny_domain_override` check still apply, but they do not enforce a per-user or per-key creation namespace.

Enabling creation does not grant access to other existing zones or enable deletion. Leave this setting disabled if ordinary Users and User-role keys should only manage their assigned zones. See [API self-service zone creation](../../API.md#self-service-zone-creation) for the endpoints and authentication methods.

allow_user_remove_domain: Same as `allow_user_create_domain` but for removing a domain.

allow_user_view_history: Allow a user with the role `user` to view and access the history.

custom_history_header: This is a string type variable, when inputting an header name, if exists in the request it will
be in the created_by column in the history, if empty or not mentioned will default to the api_key description. 

site_name: This will be the site name.
