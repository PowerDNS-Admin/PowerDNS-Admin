### API Usage

#### Getting started with docker

1. Run docker image docker-compose up, go to UI http://localhost:9191, at http://localhost:9191/swagger is swagger API specification
2. Click to register user, type e.g. user: admin and password: admin
3. Login to UI in settings enable allow domain creation for users, now you can create and manage domains with admin account and also ordinary users
4. Click on the API Keys menu then click on teh "Add Key" button to add a new Administrator Key
5. Keep the base64 encoded apikey somewhere safe as it won't be available in clear anymore


#### Accessing the API

The PDA API consists of two distinct parts:

- The /powerdnsadmin endpoints manages PDA content (accounts, users, apikeys) and also allow domain creation/deletion
- The /server endpoints are proxying queries to the backend PowerDNS instance's API. PDA acts as a proxy managing several API Keys and permissions to the PowerDNS content.

The requests to the API needs two headers:

- The classic 'Content-Type: application/json' is required to all POST and PUT requests, though it's harmless to use it on each call
- The authentication header to provide either the login:password basic authentication or the Api Key authentication.

When you access the `/powerdnsadmin` endpoint, you must use the Basic Auth:

```bash
# Encode your user and password to base64
$ echo -n 'admin:admin'|base64
YWRtaW46YWRtaW4=
# Use the ouput as your basic auth header
curl -H 'Authorization: Basic YWRtaW46YWRtaW4=' -X <method> <url>
```

When you access the `/server` endpoint, you must use the ApiKey

```bash
# Use the already base64 encoded key in your header
curl -H 'X-API-Key: YUdDdGhQM0tMQWV5alpJ' -X <method> <url>
```

Finally, the `/sync_domains` endpoint accepts both basic and apikey authentication

#### Examples

Creating domain via `/powerdnsadmin`:

```bash
curl -L -vvv -H 'Content-Type: application/json' -H 'Authorization: Basic YWRtaW46YWRtaW4=' -X POST http://localhost:9191/api/v1/pdnsadmin/zones --data '{"name": "yourdomain.com.", "kind": "NATIVE", "nameservers": ["ns1.mydomain.com."]}'
```

Creating an apikey which has the Administrator role:

```bash
# Create the key
curl -L -vvv -H 'Content-Type: application/json' -H 'Authorization: Basic YWRtaW46YWRtaW4=' -X POST http://localhost:9191/api/v1/pdnsadmin/apikeys --data '{"description": "masterkey","domains":[], "role": "Administrator"}'
```
Example response (don't forget to save the plain key from the output)

```json
[
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
]
```

We can use the apikey for all calls to PowerDNS (don't forget to specify Content-Type):

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
