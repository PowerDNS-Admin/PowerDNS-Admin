# Running PowerDNS-Admin on Docker

The official Docker image for PowerDNS-Admin is available on Docker Hub as `powerdnsadmin/pda-legacy`.

For a list of supported environment variables that can be used to configure the container, please see the [Environment Variables](../configuration/Environment-variables.md) documentation.

To run the container and expose the web server on port 9191, you can use the following command:

```bash
docker run -d \
    -e SECRET_KEY='a-very-secret-key' \
    -v pda-data:/data \
    -p 9191:80 \
    powerdnsadmin/pda-legacy:latest
```
