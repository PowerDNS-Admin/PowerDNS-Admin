This document describes how to build and debug the PowerDNS-Admin Docker image.

## Production Build

The production Docker image is built using the `docker/common/Dockerfile.app` file and is orchestrated by the `.github/workflows/build-and-publish.yml` GitHub Actions workflow.

### Image Naming

The primary Docker image is published to Docker Hub as `powerdnsadmin/pda-legacy`. While the name includes "legacy," this is the current, actively maintained image. The name is a historical artifact.

### Local Building and Testing

To build the image locally for testing or development, you can use the `docker-compose-dev.yml` file.

```console
# From the root of the project
docker-compose -f docker/docker-compose-dev.yml up --build
```

This command will build the `app` service using the `docker/common/Dockerfile.app` file and start the necessary services for a development environment.

## Debugging

For debugging purposes, you can modify the `docker-compose-dev.yml` file to override the default command and keep the container running.

For example, you can change the `command` for the `app` service to `tail -f /dev/null`:

```yaml
services:
  app:
    # ... other service configuration
    command: tail -f /dev/null
```

This will start the container and keep it running, allowing you to get a shell inside it for debugging:

```console
docker-compose -f docker/docker-compose-dev.yml exec app /bin/bash
```
