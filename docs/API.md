### API Usage

#### Getting started with docker

1. Run docker image docker-compose up, go to UI http://localhost:9191, at http://localhost:9191/swagger is swagger API specification
2. Click to register user, type e.g. user: admin and password: admin
3. Login to UI in settings enable allow domain creation for users, now you can create and manage domains with admin account and also ordinary users
4. As an Administrator, click the API Keys menu and then "Add Key" to add a new Administrator key.
5. Keep the Base64-encoded API key somewhere safe. It is returned only once and cannot be retrieved again.


#### Accessing the API

PDA has its own API, that should not be confused with the PowerDNS API. Keep in mind that you have to enable PowerDNS API with a key that will be used by PDA to manage it. Therefore, you should use PDA created keys to browse PDA's API, on PDA's adress and port. They don't grant access to PowerDNS' API.

The PDA API consists of two distinct parts:

- The `/pdnsadmin` endpoints manage PDA content (accounts, users, API keys) and also allow domain creation and deletion.
- The `/servers` endpoints proxy queries to the backend PowerDNS API. PDA applies its API-key roles and zone permissions before forwarding a request.

The requests to the API needs two headers:

- The classic 'Content-Type: application/json' is required to all POST and PUT requests, though it's harmless to use it on each call
- The authentication header to provide either the login:password basic authentication or the Api Key authentication.

When you access a `/pdnsadmin` endpoint, you must use Basic authentication:

```bash
# Encode your user and password to base64
$ echo -n 'admin:admin'|base64
YWRtaW46YWRtaW4=
# Use the ouput as your basic auth header
curl -H 'Authorization: Basic YWRtaW46YWRtaW4=' -X <method> <url>
```

When you access a `/servers` endpoint, you must use an API key:

```bash
# Use the already base64 encoded key in your header
curl -H 'X-API-Key: YUdDdGhQM0tMQWV5alpJ' -X <method> <url>
```

The `/sync_domains` endpoint accepts either Basic authentication or an API
key, but the credential must have the Administrator or Operator role.

API authorization always follows the credential sent with the API request.
An existing browser login session does not raise or otherwise change the
credential's privileges.

API-key role grants follow these rules:

- Administrators may create or grant Administrator, Operator, and User keys.
- Operators may create or grant Operator and User keys, but never Administrator keys.
- Ordinary Users may create only User keys for zones they can access and cannot assign accounts.

API-key list and detail responses contain metadata only. They never contain
the plaintext key or its stored verifier. The plaintext `plain_key` field is
returned exactly once by the create operation.

For Basic-authenticated zone deletion, Administrators and Operators may
remove zones. An ordinary User may remove only an assigned zone and only when
the `allow_user_remove_domain` setting is enabled. Enabling
`allow_user_create_domain` does not enable deletion.

#### Examples

Creating a domain via `/pdnsadmin`:

```bash
curl -L -vvv -H 'Content-Type: application/json' -H 'Authorization: Basic YWRtaW46YWRtaW4=' -X POST http://localhost:9191/api/v1/pdnsadmin/zones --data '{"name": "yourdomain.com.", "kind": "NATIVE", "nameservers": ["ns1.mydomain.com."]}'
```

Creating an API key with the Administrator role (Administrator credentials are required):

```bash
# Create the key
curl -L -vvv -H 'Content-Type: application/json' -H 'Authorization: Basic YWRtaW46YWRtaW4=' -X POST http://localhost:9191/api/v1/pdnsadmin/apikeys --data '{"description": "masterkey","domains":[], "role": "Administrator"}'
```
Example response (save `plain_key` securely):

```json
{
  "accounts": [],
  "description": "masterkey",
  "domains": [],
  "role": {
    "name": "Administrator",
    "id": 1
  },
  "id": 2,
  "plain_key": "aGCthP3KLAeyjZI"
}
```

Administrator API keys are required for server metadata endpoints such as
`/servers` and `/servers/{server_id}`:

Getting powerdns configuration (Administrator Key is needed):

```bash
curl -L -vvv -H 'Content-Type: application/json' -H 'X-API-KEY: YUdDdGhQM0tMQWV5alpJ' -X GET http://localhost:9191/api/v1/servers/localhost/config
```

Creating and updating records:

```bash
curl -X PATCH -H 'Content-Type: application/json' --data '{"rrsets": [{"name": "test1.yourdomain.com.","type": "A","ttl": 86400,"changetype": "REPLACE","records": [ {"content": "192.0.2.5", "disabled": false} ]},{"name": "test2.yourdomain.com.","type": "AAAA","ttl": 86400,"changetype": "REPLACE","records": [ {"content": "2001:db8::6", "disabled": false} ]}]}' -H 'X-API-Key: YUdDdGhQM0tMQWV5alpJ' http://127.0.0.1:9191/api/v1/servers/localhost/zones/yourdomain.com.
```

Getting a domain:

```bash
curl -L -vvv -H 'Content-Type: application/json' -H 'X-API-KEY: YUdDdGhQM0tMQWV5alpJ' -X GET http://localhost:9191/api/v1/servers/localhost/zones/yourdomain.com
```

List a zone's records:

```bash
curl -H 'Content-Type: application/json' -H 'X-API-Key: YUdDdGhQM0tMQWV5alpJ' http://localhost:9191/api/v1/servers/localhost/zones/yourdomain.com
```

Add a new record:

```bash
curl -H 'Content-Type: application/json' -X PATCH --data '{"rrsets": [ {"name": "test.yourdomain.com.", "type": "A", "ttl": 86400, "changetype": "REPLACE", "records": [ {"content": "192.0.5.4", "disabled": false } ] } ] }' -H 'X-API-Key: YUdDdGhQM0tMQWV5alpJ' http://localhost:9191/api/v1/servers/localhost/zones/yourdomain.com | jq .
```

Update a record:

```bash
curl -H 'Content-Type: application/json' -X PATCH --data '{"rrsets": [ {"name": "test.yourdomain.com.", "type": "A", "ttl": 86400, "changetype": "REPLACE", "records": [ {"content": "192.0.2.5", "disabled": false, "name": "test.yourdomain.com.", "ttl": 86400, "type": "A"}]}]}' -H 'X-API-Key: YUdDdGhQM0tMQWV5alpJ' http://localhost:9191/api/v1/servers/localhost/zones/yourdomain.com | jq .
```

Delete a record:

```bash
curl -H 'Content-Type: application/json' -X PATCH --data '{"rrsets": [ {"name": "test.yourdomain.com.", "type": "A", "ttl": 86400, "changetype": "DELETE"}]}' -H 'X-API-Key: YUdDdGhQM0tMQWV5alpJ' http://localhost:9191/api/v1/servers/localhost/zones/yourdomain.com | jq
```

### Generate ER diagram

With docker

```bash
# Install build packages
apt-get install python-dev graphviz libgraphviz-dev pkg-config
# Get the required python libraries
pip install graphviz mysqlclient ERAlchemy
# Start the docker container
docker-compose up -d
# Set environment variables
source .env
# Generate the diagrams
eralchemy -i 'mysql://${PDA_DB_USER}:${PDA_DB_PASSWORD}@'$(docker inspect powerdns-admin-mysql|jq -jr '.[0].NetworkSettings.Networks.powerdnsadmin_default.IPAddress')':3306/powerdns_admin' -o /tmp/output.pdf
```
