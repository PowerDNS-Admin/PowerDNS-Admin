### Docker development and test environments

Development, Python testing, and browser testing are separate Compose projects.
They have independent service names, images, networks, entrypoints, and data.
Running or tearing down one scenario cannot select a mode in or remove another.

All application, Python, asset, and browser dependencies are installed inside
Docker images. No host `node_modules` directory is required or created.

#### Development inspection

The development scenario lives in `docker-dev/` and reuses the persistent
application database volume from the former combined Compose project:

```console
docker compose -f docker-compose-dev.yml up --build
```

PowerDNS-Admin is available at <http://localhost:9191> and PowerDNS at
<http://localhost:8081>. Stop only this scenario with:

```console
docker compose -f docker-compose-dev.yml down
```

#### Python test suite

The Python-only scenario lives in `docker-test/`. It has no host ports or
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

The full-stack scenario lives in `docker-browser-test/`:

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
