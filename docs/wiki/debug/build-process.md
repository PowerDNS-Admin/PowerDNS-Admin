This document describes how to build and debug the PowerDNS-Admin Docker image.

## Production Build

The production Docker image is built using the `docker/common/Dockerfile.app` file and is orchestrated by the `.github/workflows/build-and-publish.yml` GitHub Actions workflow.

### Image Naming

The primary Docker image is published to Docker Hub as `powerdnsadmin/pda-legacy`. While the name includes "legacy," this is the current, actively maintained image. The name is a historical artifact.

### Local Building and Testing

To build and run the production image from the checked-out source, use the default Compose file. This stack also starts a persistent MySQL 8.4 service and waits for it to become healthy before starting PowerDNS-Admin.

```console
# From the root of the project
docker compose -f docker/docker-compose.yml up --build
```

The `app` service builds `docker/common/Dockerfile.app` with `DOCKER_SCENARIO=production`. For application development and the complete PowerDNS-backed environment, use `docker/docker-compose-dev.yml` as described in the [test and development guide](../../running_tests.md).

## Debugging

For debugging purposes, you can modify `docker/docker-compose-dev.yml` to override the default command and keep the container running.

For example, you can change the command for the `powerdns-admin` service to `tail -f /dev/null`:

```yaml
services:
  powerdns-admin:
    # ... other service configuration
    command: tail -f /dev/null
```

This will start the container and keep it running, allowing you to get a shell inside it for debugging:

```console
docker compose -f docker/docker-compose-dev.yml exec powerdns-admin /bin/sh
```
