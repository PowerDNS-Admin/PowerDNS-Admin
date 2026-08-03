const { defineConfig, devices } = require('@playwright/test');

const baseURL = process.env.BASE_URL || 'http://powerdns-admin';
const projects = [];
const smokeTest = process.env.BROWSER_TEST_SMOKE === '1';

for (const colorScheme of smokeTest ? ['light'] : ['light', 'dark']) {
  projects.push(
    {
      name: `chrome-${colorScheme}`,
      use: { ...devices['Desktop Chrome'], channel: 'chrome', colorScheme },
    },
  );

  if (!smokeTest) {
    projects.push(
      {
        name: `edge-${colorScheme}`,
        use: { ...devices['Desktop Edge'], channel: 'msedge', colorScheme },
      },
      {
        name: `firefox-${colorScheme}`,
        use: { ...devices['Desktop Firefox'], colorScheme },
      },
    );
  }
}

module.exports = defineConfig({
  testDir: './tests',
  outputDir: './test-results',
  fullyParallel: false,
  workers: 1,
  retries: 1,
  timeout: 45_000,
  reporter: [
    ['line'],
    ['html', { outputFolder: './playwright-report', open: 'never' }],
    ['./console-reporter.js', {
      outputFile: './test-results/browser-console-diagnostics.json',
    }],
  ],
  use: {
    baseURL,
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure',
    video: 'retain-on-failure',
  },
  projects: [
    {
      name: 'setup',
      testMatch: /global\.setup\.js/,
      use: { ...devices['Desktop Chrome'], channel: 'chrome' },
    },
    ...projects.map((project) => ({
      ...project,
      dependencies: ['setup'],
      use: { ...project.use, storageState: './test-results/auth.json' },
    })),
  ],
  expect: { timeout: 10_000 },
});
