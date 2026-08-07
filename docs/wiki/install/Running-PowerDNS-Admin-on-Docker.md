# Running PowerDNS-Admin on Docker

The official Docker image for PowerDNS-Admin is available on Docker Hub as `powerdnsadmin/pda-legacy`.

For a list of supported environment variables that can be used to configure the container, please see the [Environment Variables](../configuration/Environment-variables.md) documentation.

## Run the Docker Hub image

The standalone image uses SQLite by default. The following command stores its database in a named volume and exposes the web server on port 9191:

```bash
docker run -d \
    -e SECRET_KEY='a-very-secret-key' \
    -v pda-data:/data \
    -p 9191:80 \
    powerdnsadmin/pda-legacy:latest
```

## Build with Docker Compose

The repository's production Compose configuration builds the checked-out source and starts MySQL 8.4 alongside PowerDNS-Admin. MySQL data is persisted in the `pda-mysql` named volume, and the application waits for MySQL to become healthy before it runs database migrations and starts Gunicorn.

Before deploying, replace the example database passwords in `docker/docker-compose.yml` and set `SECRET_KEY` to a long, random value. Then run this command from the repository root:

```bash
docker compose -f docker/docker-compose.yml up --build
```

PowerDNS-Admin is available at <http://localhost:9191>.

To stop the stack without deleting its MySQL data:

```bash
docker compose -f docker/docker-compose.yml down
```

Adding `--volumes` to the `down` command permanently deletes the Compose stack's MySQL data.
