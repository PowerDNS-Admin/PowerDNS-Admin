### Docker Development and Test Environments

The development, Python testing, and browser testing environments are managed as separate Compose projects. Each has its own service names, images, networks, entrypoints, and data. This ensures that running or tearing down one environment will not affect the others.

All application, Python, asset, and browser dependencies are installed within their respective Docker images. No `node_modules` directory is created on the host.

All `docker compose` commands should be run from the project root.

#### Development Environment

The development environment is located in the `docker/dev/` directory. Its MySQL and PostgreSQL data is stored in named volumes, which means that recreating the application container will not affect the databases.

To start the development environment, run the following command:

```console
docker compose -f docker/docker-compose-dev.yml up --build
```

PowerDNS-Admin will be available at <http://localhost:9191>, and PowerDNS will be available at <http://localhost:8081>.

To stop the development environment, run:

```console
docker compose -f docker/docker-compose-dev.yml down
```

##### Testing In-Place Upgrades

The `PDA_IMAGE` feature gate allows you to select a published PowerDNS-Admin image instead of the default `powerdns-admin-dev` image. This is useful for testing in-place upgrades by initializing the database with an older release, adding data, and then running the current version's migrations against that database.

To start with a clean v0.4.2 baseline, first remove the existing development containers and volumes, pull the desired release, and then start the environment without building the local application image:

```console
# WARNING: The --volumes flag will delete both development database volumes and their data.
docker compose -f docker/docker-compose-dev.yml down --volumes
docker pull powerdnsadmin/pda-legacy:v0.4.2
docker compose -f docker/docker-compose-dev.yml build terraform-pdns-seed
PDA_IMAGE=powerdnsadmin/pda-legacy:v0.4.2 \
  docker compose -f docker/docker-compose-dev.yml up -d --no-build
```

Wait for the older release to complete its migrations, then use the web interface at <http://localhost:9191> to create or import the data you want to preserve during the upgrade. You can monitor the startup process with the following command:

```console
docker compose -f docker/docker-compose-dev.yml logs -f powerdns-admin
```

Next, build the current working tree and recreate only the application service. Do not set `PDA_IMAGE` for these commands, as the default value selects the local `powerdns-admin-dev` image. The `--no-deps` flag leaves the running database containers and their named volumes in place.

```console
docker compose -f docker/docker-compose-dev.yml build powerdns-admin
docker compose -f docker/docker-compose-dev.yml up -d \
  --no-deps --force-recreate powerdns-admin
docker compose -f docker/docker-compose-dev.yml logs -f powerdns-admin
```

The recreated application will run `flask db upgrade` on startup. After it is healthy, you should verify that the expected migration revisions are present in the logs and that your pre-upgrade data is still intact through the UI or API. Use the `down` command without the `--volumes` flag between runs to retain the database. If you already have a volume with data at the desired schema revision, you can skip the destructive baseline reset.

##### Seeding a Large PowerDNS Dataset with Terraform

The development environment includes a one-shot Terraform service for load and migration testing. By default, it manages 10,000 deterministic Native zones under `terraform.test.`, with 20 A-record RRsets in each zone. Its state is stored in the `powerdns-admin-dev-terraform` named volume, so subsequent runs will converge the existing dataset instead of creating duplicates.

The standard development command will build and run the seeder automatically. The PowerDNS-Admin service will only start after the Terraform apply has succeeded:

```console
docker compose -f docker/docker-compose-dev.yml up --build
```

The service accepts the PowerDNS API v1 URL and API key via the `PDNS_SERVER_URL` and `PDNS_API_KEY` environment variables. The Compose defaults target the development PowerDNS service at `http://pdns-server:8081/api/v1` with the key `changeme`. You can also tune the dataset and apply concurrency:

```console
PDNS_SERVER_URL=http://pdns-server:8081/api/v1 \
PDNS_API_KEY=changeme \
TF_ZONE_COUNT=10000 \
TF_RECORDS_PER_ZONE=20 \
TF_ZONE_SUFFIX=terraform.test. \
TF_RECORD_TTL=300 \
TF_PARALLELISM=50 \
  docker compose -f docker/docker-compose-dev.yml up --build
```

The default plan manages 210,000 Terraform resources and can take a significant amount of time and memory to apply. For a quicker smoke test, use smaller values for `TF_ZONE_COUNT` and `TF_RECORDS_PER_ZONE`.

Removing the Terraform state volume will not remove the zones from PowerDNS. To remove the generated data, you must run `terraform destroy` with the same configuration.

```console
TF_COMMAND=destroy \
TF_ZONE_COUNT=10000 \
TF_RECORDS_PER_ZONE=20 \
  docker compose -f docker/docker-compose-dev.yml run --rm terraform-pdns-seed
```

#### Python Test Suite

The Python-only test environment is located in `docker/test/`. It does not expose any host ports, does not have a persistent application volume, and starts PowerDNS with a clean schema.

To run the Python test suite, use the following command:

```console
docker compose -f docker/docker-compose-test.yml up \
  --build --force-recreate --abort-on-container-exit \
  --exit-code-from python-tests
```

To remove the test environment's containers and network, run:

```console
docker compose -f docker/docker-compose-test.yml down
```

#### Full Browser Test Suite

The full-stack browser test environment is located in `docker/browser-test/`.

To run the full browser test suite, use the following command:

```console
docker compose -f docker/docker-compose-browser-test.yml up \
  --build --force-recreate --abort-on-container-exit \
  --exit-code-from browser-tests
```

This environment resets its own PowerDNS database, migrates and seeds its own PowerDNS-Admin database, verifies the API connection to PowerDNS, starts the web application, and runs the complete Python test suite. Only after these checks pass does it run the signed-in Chrome, Edge, and Firefox tests in both light and dark modes. The browser setup creates a zone through the UI and confirms it directly through the PowerDNS API.

The browser dependencies and `node_modules` exist only in the browser-runner image. The runner uses the `linux/amd64` platform because stable Linux packages for Chrome and Edge are not published for ARM. Docker Desktop will emulate this on ARM hosts.

Screenshots and failure artifacts are written to the `test-results/browser` directory, and the HTML report is written to `playwright-report`. Both of these directories are ignored by Git.

To remove the browser test environment, run:

```console
docker compose -f docker/docker-compose-browser-test.yml down
```
