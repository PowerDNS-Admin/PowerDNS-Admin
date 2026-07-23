FROM mcr.microsoft.com/playwright:v1.61.0-noble

WORKDIR /tests

COPY package.json .yarnrc.yml ./
RUN corepack enable \
    && yarn install \
    && yarn playwright install chrome msedge \
    && yarn cache clean

COPY playwright.config.js ./
COPY tests ./tests

CMD ["yarn", "test"]
