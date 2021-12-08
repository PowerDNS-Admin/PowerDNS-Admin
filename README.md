# PowerDNS-Admin

[![Language grade: Python](https://img.shields.io/lgtm/grade/python/g/ngoduykhanh/PowerDNS-Admin.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/ngoduykhanh/PowerDNS-Admin/context:python)
[![Language grade: JavaScript](https://img.shields.io/lgtm/grade/javascript/g/ngoduykhanh/PowerDNS-Admin.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/ngoduykhanh/PowerDNS-Admin/context:javascript)

The PowerDNS-Admin is a simple web GUI for managing zone configurations of a PowerDNS Authoritative server.

The PowerDNS-Admin app does NOT modify the PowerDNS Authoritative server database directly. Instead, it communicates with the PDNS server via the built-in HTTP API.

The app does have a database for identity management, access control, and caching which can be hosted in either MySQL or SQLite.

- [PowerDNS-Admin GitHub](https://github.com/ngoduykhanh/PowerDNS-Admin)
- [PowerDNS-Admin Settings](https://github.com/ngoduykhanh/PowerDNS-Admin/blob/master/docs/settings.md)
- [PowerDNS-Admin Wiki](https://github.com/ngoduykhanh/PowerDNS-Admin/wiki)

#### Features:
- Multiple domain management
- Domain template
- User management
- User access management based on domain
- User activity logging
- Support Local DB / SAML / LDAP / Active Directory user authentication
- Support Google / Github / Azure / OpenID OAuth
- Support Two-factor authentication (TOTP)
- Dashboard and pdns service statistics
- DynDNS 2 protocol support
- Edit IPv6 PTRs using IPv6 addresses directly (no more editing of literal addresses!)
- Limited API for manipulating zones and records
- Full IDN/Punycode support

## Deploying PowerDNS-Admin
There are multiple ways to run the PowerDNS-Admin app. The recommended method is to use the official [Docker images](https://github.com/ngoduykhanh/PowerDNS-Admin/blob/master/docs/docker.md).

If you would like to run PowerDNS-Admin directly on your machine or VM, check out the [Wiki](https://github.com/ngoduykhanh/PowerDNS-Admin/wiki#installation-guides) for additional information.

Once you have deployed the app through one of the supported methods, You should be able to access the PowerDNS-Admin app by pointing your browser to http://localhost:8080.

## Configuring PowerDNS-Admin

The app has a [plethora of settings](https://github.com/ngoduykhanh/PowerDNS-Admin/blob/master/docs/settings.md) that may be configured through a number of methods. Check out the settings documentation [here](https://github.com/ngoduykhanh/PowerDNS-Admin/blob/master/docs/settings.md).

[PowerDNS Admin Settings](https://github.com/ngoduykhanh/PowerDNS-Admin/blob/master/docs/settings.md)

## Screenshots
![dashboard](https://user-images.githubusercontent.com/6447444/44068603-0d2d81f6-9fa5-11e8-83af-14e2ad79e370.png)

## LICENSE
MIT. See [LICENSE](https://github.com/ngoduykhanh/PowerDNS-Admin/blob/master/LICENSE)

## Support
If you like the project and want to support it, you can *buy me a coffee* ☕

<a href="https://www.buymeacoffee.com/khanhngo" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-orange.png" alt="Buy Me A Coffee" height="41" width="174"></a>
