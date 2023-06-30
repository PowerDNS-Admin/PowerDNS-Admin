Usage:  
IPv4: http://user:pass@yournameserver.yoursite.tld/nic/update?hostname=record.domain.tld&myip=127.0.0.1  
IPv6: http://user:pass@yournameserver.yoursite.tld/nic/update?hostname=record.domain.tld&myip=::1  
Multiple IPs: http://user:pass@yournameserver.yoursite.tld/nic/update?hostname=record.domain.tld&myip=127.0.0.1,127.0.0.2,::1,::2

Notes:
- user needs to be a LOCAL user, not LDAP etc
- user must have already logged-in
- user needs to be added to Domain Access Control list of domain.tld - admin status (manage all) does not suffice
- record has to exist already - unless on-demand creation is allowed
- ipv4 address in myip field will change A record
- ipv6 address in myip field will change AAAA record
- use commas to separate multiple IP addresses in the myip field, mixing v4 & v6 is allowed

DynDNS also works without authentication header (user:pass@) when already authenticated via session cookie from /login, even with external auth like LDAP.
However Domain Access Control restriction still applies.