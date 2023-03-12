### PowerDNSAdmin basic settings

PowerDNSAdmin has many features and settings available to be turned either off or on.
In this docs those settings will be explain.
To find the settings in the the dashboard go to settings>basic.

allow_user_create_domain: This setting is used to allow users with the `user` role to create a domain, not possible by
default.

allow_user_remove_domain: Same as `allow_user_create_domain` but for removing a domain.

allow_user_view_history: Allow a user with the role `user` to view and access the history.

custom_history_header: This is a string type variable, when inputting an header name, if exists in the request it will
be in the created_by column in the history, if empty or not mentioned will default to the api_key description. 

site_name: This will be the site name.
