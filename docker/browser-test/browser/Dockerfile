FROM mcr.microsoft.com/playwright:v1.62.1-noble

WORKDIR /tests

COPY docker/browser-test/browser/package.json \
    docker/browser-test/browser/.yarnrc.yml ./
RUN corepack enable \
    && yarn install \
    && yarn playwright install chrome msedge \
    && yarn cache clean

COPY browser-support.json ./
COPY docker/browser-test/browser/playwright.config.js \
    docker/browser-test/browser/console-audit.js \
    docker/browser-test/browser/console-reporter.js ./
COPY docker/browser-test/browser/tests ./tests

CMD ["yarn", "test"]
