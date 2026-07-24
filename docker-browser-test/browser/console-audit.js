const fs = require('node:fs');
const path = require('node:path');
const { test: base, expect } = require('@playwright/test');

const supportPolicy = JSON.parse(
  fs.readFileSync(path.resolve(__dirname, 'browser-support.json'), 'utf8'),
);

function browserFamily(projectName, browserTypeName) {
  if (projectName.startsWith('edge-')) {
    return 'edge';
  }
  if (projectName.startsWith('chrome-') || projectName === 'setup') {
    return 'chrome';
  }
  return browserTypeName;
}

function matchesExpected(entry, expectedMessages) {
  return expectedMessages.some(({ source, type, url, pattern }) => (
    (!source || source === entry.source)
    && (!type || type === entry.type)
    && (!url || (typeof url === 'string'
      ? entry.url === url
      : url.test(entry.url)))
    && (typeof pattern === 'string'
      ? entry.text === pattern
      : pattern.test(entry.text))
  ));
}

function normalizedDiagnosticText(text) {
  return text.replace(/glyph \d+/g, 'glyph <number>');
}

const test = base.extend({
  consoleAudit: async ({ browser }, use, testInfo) => {
    const entries = new Map();
    const expectedMessages = [
      {
        type: 'warning',
        pattern: /Password fields present on an insecure \(http:\/\/\) page\./,
      },
      {
        source: 'console',
        type: 'warning',
        url: 'debugger eval code',
        pattern: /Layout was forced before the page was fully loaded\./,
      },
    ];
    const monitoredPages = new WeakSet();
    const family = browserFamily(
      testInfo.project.name,
      browser.browserType().name(),
    );
    const browserVersion = browser.version();

    function recordDiagnostic(entry) {
      const normalizedEntry = {
        ...entry,
        text: normalizedDiagnosticText(entry.text),
      };
      const key = [
        normalizedEntry.source,
        normalizedEntry.type,
        normalizedEntry.text,
      ].join('\u0000');
      const existing = entries.get(key);
      if (existing) {
        existing.count += 1;
        return;
      }
      entries.set(key, { ...normalizedEntry, count: 1 });
    }

    const consoleAudit = {
      expectMessage(pattern, options = {}) {
        expectedMessages.push({
          pattern,
          source: options.source,
          type: options.type,
          url: options.url,
        });
      },
      monitorPage(page) {
        if (monitoredPages.has(page)) {
          return;
        }
        monitoredPages.add(page);

        page.on('console', (message) => {
          if (!['warning', 'error'].includes(message.type())) {
            return;
          }
          const location = message.location();
          recordDiagnostic({
            source: 'console',
            type: message.type(),
            text: message.text(),
            url: location.url || page.url(),
            line: location.lineNumber ?? null,
            column: location.columnNumber ?? null,
          });
        });

        page.on('pageerror', (error) => {
          recordDiagnostic({
            source: 'pageerror',
            type: 'error',
            text: error.message,
            url: page.url(),
            line: null,
            column: null,
          });
        });
      },
    };

    await use(consoleAudit);

    const diagnostics = [...entries.values()].map((entry) => ({
      ...entry,
      expected: matchesExpected(entry, expectedMessages),
    }));
    const minimumVersion = supportPolicy.browsers[family]?.minimum_version;
    const payload = {
      project: testInfo.project.name,
      browser: {
        family,
        version: browserVersion,
        minimum_supported_version: minimumVersion || null,
      },
      test: testInfo.titlePath.join(' > '),
      retry: testInfo.retry,
      diagnostics,
    };

    await testInfo.attach('browser-console-diagnostics', {
      body: Buffer.from(JSON.stringify(payload, null, 2)),
      contentType: 'application/json',
    });

    if (minimumVersion) {
      const actualMajor = Number.parseInt(browserVersion, 10);
      const minimumMajor = Number.parseInt(minimumVersion, 10);
      expect(
        actualMajor,
        `${family} ${browserVersion} is below the supported minimum ${minimumVersion}`,
      ).toBeGreaterThanOrEqual(minimumMajor);
    }

    const unexpected = diagnostics.filter((entry) => !entry.expected);
    expect(
      unexpected,
      unexpected.map((entry) => (
        `${entry.type} (x${entry.count}): ${entry.text} `
        + `(${entry.url}:${entry.line}:${entry.column})`
      )).join('\n'),
    ).toEqual([]);
  },

  _automaticConsoleAudit: [
    async ({ page, consoleAudit }, use) => {
      consoleAudit.monitorPage(page);
      await use();
    },
    { auto: true },
  ],
});

module.exports = {
  expect,
  test,
};
