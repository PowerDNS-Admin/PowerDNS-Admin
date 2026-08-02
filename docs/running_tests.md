### Docker development and test environments

Development, Python testing, and browser testing are separate Compose projects.
They have independent service names, images, networks, entrypoints, and data.
Running or tearing down one scenario cannot select a mode in or remove another.

All application, Python, asset, and browser dependencies are installed inside
Docker images. No host `node_modules` directory is required or created.

#### Development inspection

The development scenario lives in `docker/dev/`. Its MySQL and PostgreSQL data
is stored in named volumes, so recreating the application container does not
recreate its database. Run these commands from the `docker/` directory:

```console
docker compose -f docker-compose-dev.yml up --build
```

PowerDNS-Admin is available at <http://localhost:9191> and PowerDNS at
<http://localhost:8081>. Stop only this scenario with:

```console
docker compose -f docker-compose-dev.yml down
```

##### Vet an in-place upgrade with live data

The `PDA_IMAGE` feature gate selects a published PowerDNS-Admin image instead
of the default `powerdns-admin-dev` image. This makes it possible to initialize
the persistent database with an older release, create representative data in
that release, and then run the current working tree's migrations against the
same database volume.

To start a completely clean v0.4.2 baseline, remove the development scenario's
existing containers and volumes, pull the pinned release, and start it without
building the local application image:

```console
# WARNING: --volumes deletes both development database volumes and their data.
docker compose -f docker-compose-dev.yml down --volumes
docker pull powerdnsadmin/pda-legacy:v0.4.2
docker compose -f docker-compose-dev.yml build terraform-pdns-seed
PDA_IMAGE=powerdnsadmin/pda-legacy:v0.4.2 \
  docker compose -f docker-compose-dev.yml up -d --no-build
```

Wait for the old release to finish its migrations, then use
<http://localhost:9191> to create or import the live data that the upgrade must
preserve. Its startup can be monitored with:

```console
docker compose -f docker-compose-dev.yml logs -f powerdns-admin
```

Build the current working tree and recreate only the application service. Do
not set `PDA_IMAGE` for these commands: its default value selects the local
`powerdns-admin-dev` image. `--no-deps` leaves the running database containers
and their named volumes in place.

```console
docker compose -f docker-compose-dev.yml build powerdns-admin
docker compose -f docker-compose-dev.yml up -d \
  --no-deps --force-recreate powerdns-admin
docker compose -f docker-compose-dev.yml logs -f powerdns-admin
```

The recreated application runs `flask db upgrade` during startup. After it is
healthy, verify both the expected migration revisions in the log and the
pre-upgrade data through the UI or API. Use `down` without `--volumes` between
runs when the database must be retained. If an existing volume already contains
data at the desired old schema revision, omit the destructive baseline reset.

##### Seed a large PowerDNS dataset with Terraform

The development scenario includes a one-shot Terraform service for load and
migration testing. By default it manages 10,000 deterministic Native zones
under `terraform.test.`, with 20 A-record RRsets in each zone. Its state is
stored in the `powerdns-admin-dev-terraform` named volume, so subsequent runs
converge the existing dataset instead of blindly adding duplicates.

The normal development command builds and runs the seeder automatically. The
PowerDNS-Admin service starts only after the Terraform apply succeeds:

```console
docker compose -f docker-compose-dev.yml up --build
```

The service accepts the PowerDNS API v1 URL and API key through
`PDNS_SERVER_URL` and `PDNS_API_KEY`. The Compose defaults target the development
PowerDNS service at `http://pdns-server:8081/api/v1` with the `changeme` key.
The dataset and apply concurrency can also be tuned:

```console
PDNS_SERVER_URL=http://pdns-server:8081/api/v1 \
PDNS_API_KEY=changeme \
TF_ZONE_COUNT=10000 \
TF_RECORDS_PER_ZONE=20 \
TF_ZONE_SUFFIX=terraform.test. \
TF_RECORD_TTL=300 \
TF_PARALLELISM=50 \
  docker compose -f docker-compose-dev.yml up --build
```

The default plan manages 210,000 Terraform resources and can take substantial
time and memory to apply. Use smaller `TF_ZONE_COUNT` and
`TF_RECORDS_PER_ZONE` values for a smoke test. Removing the Terraform state
volume does not remove zones from PowerDNS; run `terraform destroy` through the
same configuration before deleting state when the generated data must also be
removed. Pass the same dataset settings used during apply when they differed
from the defaults:

```console
TF_COMMAND=destroy \
TF_ZONE_COUNT=10000 \
TF_RECORDS_PER_ZONE=20 \
  docker compose -f docker-compose-dev.yml run --rm terraform-pdns-seed
```

#### Python test suite

The Python-only scenario lives in `docker/test/`. It has no host ports or
persistent application volume and starts PowerDNS from a clean schema:

```console
docker compose -f docker-compose-test.yml up \
  --build --force-recreate --abort-on-container-exit \
  --exit-code-from python-tests
```

Remove only its containers and network with:

```console
docker compose -f docker-compose-test.yml down
```

#### Full browser test suite

The full-stack scenario lives in `docker/browser-test/`:

```console
docker compose -f docker-compose-browser-test.yml up \
  --build --force-recreate --abort-on-container-exit \
  --exit-code-from browser-tests
```

This scenario resets its own PowerDNS database, migrates and seeds its own
PowerDNS-Admin database, verifies the stored API connection against live
PowerDNS, starts the real HTTP application, and runs the complete Python suite.
Only after those checks pass does it run the signed-in Chrome, Edge, and Firefox
cases in light and dark modes. Browser setup creates a zone through the UI and
confirms it directly through the PowerDNS API.

Browser dependencies and `node_modules` exist only in the browser-runner image.
The runner uses `linux/amd64` because Chrome and Edge stable Linux packages are
not published for ARM; Docker Desktop emulates it on ARM hosts.

Route screenshots and failure artifacts are written to `test-results/browser`;
the HTML report is written to `playwright-report`. Both are ignored by Git.

Remove only the full browser scenario with:

```console
docker compose -f docker-compose-browser-test.yml down
```
