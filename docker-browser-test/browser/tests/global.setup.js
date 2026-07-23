const { test: setup, expect } = require('@playwright/test');

const authFile = './test-results/auth.json';

setup('verify configured deployment and create the browser-test zone', async ({ page, request }) => {
  await page.goto('/login');
  await page.getByRole('textbox', { name: 'Username' }).fill(
    process.env.BROWSER_TEST_USERNAME || 'browser-admin',
  );
  await page.locator('input[name="password"]').fill(
    process.env.BROWSER_TEST_PASSWORD || 'BrowserTest123!',
  );
  await Promise.all([
    page.waitForURL(/\/dashboard\//),
    page.getByRole('button', { name: 'Sign In' }).click(),
  ]);

  const testZone = page.getByRole('link', { name: 'browser-test.example' });
  if (!(await testZone.count())) {
    await page.goto('/domain/add');
    await page.locator('#domain_name').fill('browser-test.example');
    await Promise.all([
      page.waitForURL(/\/dashboard\//),
      page.getByRole('button', { name: 'Create Zone' }).click(),
    ]);
  }

  const pdnsResponse = await request.get(
    `${process.env.PDNS_API_URL}/api/v1/servers/localhost/zones/browser-test.example.`,
    { headers: { 'X-API-Key': process.env.PDNS_API_KEY } },
  );
  expect(pdnsResponse.status()).toBe(200);
  const pdnsZone = await pdnsResponse.json();
  expect(pdnsZone.name).toBe('browser-test.example.');

  await page.goto('/admin/setting/pdns');
  await expect(page.locator('input[name="pdns_api_url"]')).toHaveValue(
    process.env.EXPECTED_PDNS_API_URL,
  );
  await expect(page.locator('input[name="pdns_api_key"]')).toHaveValue(
    process.env.PDNS_API_KEY,
  );
  await expect(page.locator('body')).toBeVisible();
  await page.context().storageState({ path: authFile });
});
