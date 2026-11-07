# Running PowerDNS-Admin on Docker

The official Docker image for PowerDNS-Admin is available on Docker Hub as `powerdnsadmin/pda-legacy`.

For a list of supported environment variables that can be used to configure the container, please see the [Environment Variables](../configuration/Environment-variables.md) documentation.

## Run the Docker Hub image

PowerDNS-Admin requires an explicit database configuration. Startup refuses a missing, short, or published `SECRET_KEY`. It must be at least 32 characters. Startup validates `SALT` with bcrypt and refuses a missing or unusable salt. Use `bcrypt.gensalt()` to generate a salt for a new deployment, as shown below.

For an existing deployment, keep its current valid `SALT`: it does not need to be private, and the published salt is accepted with a warning. Changing `SALT` invalidates existing API keys and outstanding email-confirmation links. Keep both configuration values stable across container restarts. See the [environment variables documentation](../configuration/Environment-variables.md) for details.

The following example selects SQLite, stores its database in a named volume, and exposes the web server on port 9191:

```bash
docker pull powerdnsadmin/pda-legacy:latest
export SECRET_KEY="$(python3 -c 'import secrets; print(secrets.token_hex(32))')"
export SALT="$(docker run --rm --entrypoint python powerdnsadmin/pda-legacy:latest -c 'import bcrypt; print(bcrypt.gensalt().decode())')"
docker run -d \
    -e SECRET_KEY \
    -e SALT \
    -e SQLALCHEMY_DATABASE_URI='sqlite:////data/powerdns-admin.db' \
    -v pda-data:/data \
    -p 9191:80 \
    powerdnsadmin/pda-legacy:latest
```

## Build with Docker Compose

The repository's production Compose configuration builds the checked-out source and starts MySQL 8.4 alongside PowerDNS-Admin. MySQL data is persisted in the `pda-mysql` named volume, and the application waits for MySQL to become healthy before it runs database migrations and starts Gunicorn.

Before deploying, replace the example database passwords in `docker/docker-compose.yml`. Export `SECRET_KEY` and `SALT` in the shell first, using the commands above. The Compose file reads those variables. A bcrypt salt contains `$`, so leave it in the environment. A literal `$` in the Compose file is treated as interpolation. Then run this command from the repository root:

```bash
docker compose -f docker/docker-compose.yml up --build
```

PowerDNS-Admin is available at <http://localhost:9191>.

To stop the stack without deleting its MySQL data:

```bash
docker compose -f docker/docker-compose.yml down
```

Adding `--volumes` to the `down` command permanently deletes the Compose stack's MySQL data.
