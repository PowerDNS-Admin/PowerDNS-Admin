const { test: setup, expect } = require('../console-audit');

const authFile = './test-results/auth.json';
const adminUsername = process.env.BROWSER_TEST_USERNAME || 'browser-admin';
const adminPassword = process.env.BROWSER_TEST_PASSWORD || 'BrowserTest123!';
const roleSecurityUsers = [
  {
    username: 'browser-role-operator',
    password: 'BrowserOperator123!',
    roleName: 'Operator',
  },
  {
    username: 'browser-role-user',
    password: 'BrowserUser123!',
    roleName: 'User',
  },
  {
    username: 'browser-role-operator-target',
    password: 'BrowserOperatorTarget123!',
    roleName: 'Operator',
  },
];

function basicAuthHeaders(username, password) {
  return {
    Authorization: `Basic ${Buffer.from(`${username}:${password}`).toString('base64')}`,
  };
}

async function ensureSecurityUser(request, user) {
  const adminHeaders = basicAuthHeaders(adminUsername, adminPassword);
  const userUrl = `/api/v1/pdnsadmin/users/${user.username}`;
  const existingResponse = await request.get(userUrl, { headers: adminHeaders });

  if (existingResponse.status() === 404) {
    const createResponse = await request.post('/api/v1/pdnsadmin/users', {
      headers: adminHeaders,
      data: {
        username: user.username,
        plain_text_password: user.password,
        email: `${user.username}@example.com`,
        confirmed: true,
        role_name: user.roleName,
      },
    });
    expect(createResponse.status()).toBe(201);
    return;
  }

  expect(existingResponse.status()).toBe(200);
  const existingUser = await existingResponse.json();
  const resetResponse = await request.put(
    `/api/v1/pdnsadmin/users/${existingUser.id}`,
    {
      headers: adminHeaders,
      data: {
        username: user.username,
        plain_text_password: user.password,
        confirmed: true,
        role_name: user.roleName,
      },
    },
  );
  expect(resetResponse.status()).toBe(204);
}

setup('verify configured deployment and create the browser-test zone', async ({ page, request }) => {
  await page.goto('/login');
  await page.getByRole('textbox', { name: 'Username' }).fill(adminUsername);
  await page.locator('input[name="password"]').fill(adminPassword);
  await Promise.all([
    page.waitForURL(/\/dashboard\//, { waitUntil: 'networkidle' }),
    page.getByRole('button', { name: 'Sign In' }).click(),
  ]);

  const testZone = page.getByRole('link', { name: 'browser-test.example' });
  if (!(await testZone.count())) {
    await page.goto('/domain/add');
    await page.locator('#domain_name').fill('browser-test.example');
    await Promise.all([
      page.waitForURL(/\/dashboard\//, { waitUntil: 'networkidle' }),
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

  for (const user of roleSecurityUsers) {
    await ensureSecurityUser(request, user);
  }

  await expect(page.locator('body')).toBeVisible();
  await page.context().storageState({ path: authFile });
});
