# Custom Roles

The Custom Roles feature introduces the ability to create new non-administrative roles, built upon the limited "User" role, in order to provide granularity in the level of control each user, or group of users, has in the application.

## Role Privileges

When editing a role, the edit-role template is comprised of 4 sections (Edit role, DNS Record Access, Access control and specific permissions control).

On the DNS Record Access, an administrative user can define the record types a user assigned to this role can access (Read or Write) for forward or reverse zones.

On the Specific Permissions control section, the role can be restricted from having the following permissions:

* History access

    * access to history of domains the user owns

* Domain creation

    * ability to create a new domain

* Domain removal

    * ability to remove a domain the user owns

* DNSSEC configuration

    * ability to toggle DNSSEC for a domain a non administrative user owns.

* View and edit all domains
    * ability to access all domains

The "View and edit all domains" setting for non-administrative users allows them to view a domain and manage its records, including creating new records and editing or deleting current records, however it does not give the user ownership of that domain. Therefore, even if the "History access" or "Domain removal" settings are enabled for a non-administrative Role, users who have this Role cannot view the history of all Domains or remove all Domains. Of course, ownership can still be granted to a user in order to have the features mentioned above.

Finally, the "Records" Setting page has been removed, along with some Basic settings regarding global User access to Domain Creation, Domain Removal, History records and DNSSEC configuration, as they were deprecated and moved to each Role's edit page.

## Compatibility with previous versions

You must execute `flask db upgrade` before running PowerDNS-Admin with the Custom Roles feature, if you are coming from a previous version.

The upgrade process does not affect existing users or existing Role behaviour. Specifically:

1. After upgrading, all users keep their existing Roles.
2. The defualt "Administrator" role behaviour remains unchanged.
3. The default "Operator" role is initially unchanged, with all the togglable features enabled.
4. The default "User" role has all options initially disabled, meaning that, for example, you will have to reselect "Allow user to create domain" for the User role, if you were using that setting previously.

**Note:** The following Settings are deprecated by this feature:
- dnssec_admins_only
- allow_user_create_domain
- allow_user_remove_domain
- allow_user_view_history

The update initially treats dnssec_admins_only as 'True' and the rest as 'False', regardless of their values before the update. Their functionality can be reverted by giving the User role the corresponding privileges.

- Record Access Settings

Previous Record Access Settings are lost, and can now be set per Role.

## Usage

### Creating a new Role
When logged in as an Administrator, or when logged in as an Operator and "Allow to edit Roles" is toggled on, you can create a new, non-administrative Role by clicking Add Role in the `/admin/manage-roles` page.

From there, you must select a Name and optionally give a Description for your new Role, set the DNS Record Access, as specified above, and set the role privileges, also as specified above. When ready, you may Create the new Role.

### Editing a Role
- A non-administrative Role can be edited by Administrators, or Operators if the "Allow to edit Roles" privilege is enabled, by pressing the Edit button on the `/admin/manage-roles` page. The resulting page is similar to the `Create Role` page, but the Role Name cannot be modified.
- For the Administrator Role, only the DNS Record Access can be edited. All permissions are force enabled for Admins.
- For the Operator Role, permissions for History Access and Viewing/Editing all Domains are force enabled. Only Administrators can Edit the Operator Role, regardless of the "Allow to edit Roles" Operator privilege value.

### Deleting a Role
- A Custom Role can be deleted by pressing the Delete button on the `/admin/manage-roles` page. You can only delete a Custom Role When logged in as an Administrator, or when logged in as an Operator and "Allow to edit Roles" is toggled on.
- The default Roles (*Administrator*, *Operator*, and *User*) **CANNOT** be deleted.

### Changing a user's Role
- A user's role can be changed by Administrators or Operators, by visiting the `/admin/manage-user` page, and selecting a different Role for the specified User from the dropdown.
- Operators cannot change the Role of administrative users, or promote non-administrative users to an administrative Role.
- You cannot change your own Role.

### API Keys
- API Keys can be created with any Custom Role.
- API Keys for non-administrative Roles may contain Domain and Accounts access information.
- If an API Key exists for a Custom Role and the Role is deleted, the API Key Role is changed to the User role.