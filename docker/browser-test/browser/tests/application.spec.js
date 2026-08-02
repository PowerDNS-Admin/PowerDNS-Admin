const { test, expect } = require('../console-audit');

const PDNS_API_URL = process.env.PDNS_API_URL || 'http://pdns-server:8081';
const PDNS_API_KEY = process.env.PDNS_API_KEY || 'changeme';
const TEST_ZONE = 'browser-test.example';
const ADMIN_USERNAME = process.env.BROWSER_TEST_USERNAME || 'browser-admin';
const ROLE_SECURITY_USERS = {
  operator: {
    username: 'browser-role-operator',
    password: 'BrowserOperator123!',
    roleName: 'Operator',
  },
  targets: [
    {
      username: 'browser-role-user',
      roleName: 'User',
    },
    {
      username: 'browser-role-operator-target',
      roleName: 'Operator',
    },
  ],
};
const pdnsHeaders = {
  'X-API-Key': PDNS_API_KEY,
  Accept: 'application/json',
};

function basicAuthHeaders(username, password) {
  return {
    Authorization: `Basic ${Buffer.from(`${username}:${password}`).toString('base64')}`,
  };
}

function collectBrowserFailures(page) {
  const failures = [];

  page.on('requestfailed', (request) => {
    const type = request.resourceType();
    if (['document', 'stylesheet', 'script', 'xhr', 'fetch'].includes(type)) {
      failures.push(
        `requestfailed: ${request.method()} ${request.url()} ${request.failure()?.errorText || ''}`,
      );
    }
  });

  return failures;
}

async function captureStep(page, testInfo, name) {
  const screenshotPath = testInfo.outputPath(`${name}.png`);
  await page.screenshot({ path: screenshotPath, fullPage: true });
  await testInfo.attach(name, {
    path: screenshotPath,
    contentType: 'image/png',
  });
}

async function removeExistingRecords(request, records) {
  const zoneUrl = `${PDNS_API_URL}/api/v1/servers/localhost/zones/${TEST_ZONE}.`;
  const zoneResponse = await request.get(zoneUrl, { headers: pdnsHeaders });
  expect(zoneResponse.ok()).toBeTruthy();

  const targetRecords = new Set(
    records.map((record) => `${record.name.toLowerCase()}.${TEST_ZONE}.|${record.type}`),
  );
  const zone = await zoneResponse.json();
  const deletions = zone.rrsets
    .filter((rrset) => targetRecords.has(`${rrset.name.toLowerCase()}|${rrset.type}`))
    .map((rrset) => ({
      name: rrset.name,
      type: rrset.type,
      changetype: 'DELETE',
      records: [],
    }));

  if (deletions.length === 0) {
    return;
  }

  const deleteResponse = await request.patch(zoneUrl, {
    headers: {
      ...pdnsHeaders,
      'Content-Type': 'application/json',
    },
    data: { rrsets: deletions },
  });
  expect(deleteResponse.status()).toBe(204);
}

async function addRecord(page, record) {
  await page.getByRole('button', { name: /Add Record/i }).click();

  const row = page.locator('#tbl_records tbody tr:has(#record_type)');
  await expect(row).toHaveCount(1);
  await row.locator('#edit-row-focus').fill(record.name);
  await row.locator('#record_type').selectOption(record.type);

  const dataInput = row.locator('#current_edit_record_data');
  if (record.type === 'TXT') {
    await dataInput.click();
    const helper = page.locator('#modal_custom_record');
    await expect(helper).toBeVisible();
    await helper.locator('#record-helper-txt-0').fill(record.value);
    await helper.getByRole('button', { name: /Save/i }).click();
    await expect(helper).toBeHidden();
  } else if (record.type === 'CAA') {
    await dataInput.click();
    const helper = page.locator('#modal_custom_record');
    await expect(helper).toBeVisible();
    await helper.locator('#record-helper-caa-0').fill(record.flag);
    await helper.locator('#record-helper-caa-1').fill(record.tag);
    await helper.locator('#record-helper-caa-2').fill(record.value);
    await helper.getByRole('button', { name: /Save/i }).click();
    await expect(helper).toBeHidden();
  } else {
    await dataInput.fill(record.value);
  }

  await row.locator('.button_save').click();
  await expect(page.locator('#unsaved-changes-banner')).toBeVisible();
}

async function getApiUser(request, username, headers) {
  const response = await request.get(
    `/api/v1/pdnsadmin/users/${username}`,
    { headers },
  );
  expect(response.status()).toBe(200);
  return response.json();
}

async function assertApiRole(request, username, roleName, headers) {
  const user = await getApiUser(request, username, headers);
  expect(user.role.name).toBe(roleName);
}

test('generated CSS avoids browser parser diagnostics', async ({ page }, testInfo) => {
  await page.goto('/dashboard/', { waitUntil: 'networkidle' });
  const stylesheetUrl = await page.locator(
    'link[rel="stylesheet"][href*="/generated/main.css"]',
  ).getAttribute('href');
  expect(stylesheetUrl).not.toBeNull();

  const response = await page.request.get(stylesheetUrl);
  expect(response.ok()).toBeTruthy();
  const css = await response.text();
  const diagnostics = [];

  const charsetOffsets = [...css.matchAll(/@charset\b/gi)]
    .map((match) => match.index)
    .filter((offset) => offset !== 0);
  if (charsetOffsets.length > 0) {
    diagnostics.push(
      `ruleset ignored: ${charsetOffsets.length} @charset rule(s) occur after the start of main.css`,
    );
  }

  if (testInfo.project.name.startsWith('firefox-')) {
    const firefoxChecks = [
      {
        pattern: /-webkit-text-size-adjust\s*:/g,
        message: 'invalid -webkit-text-size-adjust declaration',
      },
      {
        pattern: /::?-moz-focus-inner\b/g,
        message: 'unsupported -moz-focus-inner selector',
      },
      {
        pattern: /::?-moz-focus-outer\b/g,
        message: 'unsupported -moz-focus-outer selector',
      },
      {
        pattern: /prefers-contrast\s*:\s*high/g,
        message: 'invalid prefers-contrast media feature value "high"',
      },
      {
        pattern: /::-webkit-slider-thumb:active\b/g,
        message: 'unsupported -webkit-slider-thumb:active selector',
      },
    ];

    for (const check of firefoxChecks) {
      const count = [...css.matchAll(check.pattern)].length;
      if (count > 0) {
        diagnostics.push(`${check.message} (${count} occurrence(s))`);
      }
    }
  }

  await page.evaluate((messages) => {
    for (const message of messages) {
      console.warn(`stylesheet parser audit: ${message}`);
    }
  }, diagnostics);
});

test('authenticated pages render without browser or layout failures', async ({ page }, testInfo) => {
  const failures = collectBrowserFailures(page);
  const pages = [
    ['/dashboard/', 'Dashboard'],
    ['/domain/browser-test.example', 'Zone Editor'],
    ['/admin/setting/basic', 'Basic Settings'],
    ['/admin/setting/pdns', 'PowerDNS Settings'],
  ];

  for (const [url, label] of pages) {
    const response = await page.goto(url, { waitUntil: 'networkidle' });
    expect(response, `${label} should return a response`).not.toBeNull();
    expect(response.status(), `${label} status`).toBeLessThan(400);
    await expect(page.locator('.app-header')).toBeVisible();
    await expect(page.locator('.app-sidebar')).toBeVisible();
    await expect(page.locator('.app-content-header h1')).toBeVisible();
    await expect(page.locator('.breadcrumb')).toBeVisible();

    const layout = await page.evaluate(() => ({
      overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
      theme: document.documentElement.getAttribute('data-bs-theme'),
      bodyBackground: getComputedStyle(document.body).backgroundColor,
    }));
    expect(layout.overflow, `${label} has horizontal page overflow`).toBeLessThanOrEqual(1);
    expect(layout.theme).toMatch(/^(light|dark)$/);
    expect(layout.bodyBackground).not.toBe('rgba(0, 0, 0, 0)');

    await page.screenshot({
      path: testInfo.outputPath(`${label.toLowerCase().replaceAll(' ', '-')}.png`),
      fullPage: true,
    });
  }

  expect(failures, failures.join('\n')).toEqual([]);
});

test('creates and submits project-specific core DNS records', async ({ page, request }, testInfo) => {
  test.setTimeout(90_000);
  const failures = collectBrowserFailures(page);
  const projectName = testInfo.project.name;
  const records = [
    { name: `${projectName}-A`, type: 'A', value: '192.0.2.10' },
    { name: `${projectName}-AAAA`, type: 'AAAA', value: '2001:db8::10' },
    {
      name: `${projectName}-TXT`,
      type: 'TXT',
      value: `PowerDNS Admin browser test for ${projectName}`,
    },
    {
      name: `${projectName}-CNAME`,
      type: 'CNAME',
      value: `${TEST_ZONE}.`,
    },
    {
      name: `${projectName}-CAA`,
      type: 'CAA',
      flag: '0',
      tag: 'issue',
      value: 'letsencrypt.org',
    },
  ];

  await removeExistingRecords(request, records);
  await page.goto(`/domain/${TEST_ZONE}`, { waitUntil: 'networkidle' });

  for (const record of records) {
    await test.step(`create ${record.name}`, async () => {
      await addRecord(page, record);
      await captureStep(page, testInfo, `${record.name}-saved`);
    });
  }

  const banner = page.locator('#unsaved-changes-banner');
  await expect(banner).toBeVisible();

  await page.evaluate(() => {
    const spacer = document.createElement('div');
    spacer.dataset.browserTestSpacer = 'true';
    spacer.style.height = '2000px';
    document.querySelector('#zone-editor-card').after(spacer);

    const appMain = document.querySelector('.app-main');
    if (appMain && appMain.scrollHeight > appMain.clientHeight) {
      appMain.scrollTo(0, appMain.scrollHeight);
    } else {
      window.scrollTo(0, document.body.scrollHeight);
    }
  });
  await expect(banner).toHaveClass(/is-floating/);
  await banner.getByRole('button', { name: 'Review Changes' }).click();
  await expect(page.locator('#tbl_records')).toBeInViewport();

  const applyResponsePromise = page.waitForResponse(
    (response) => response.url().includes(`/domain/${TEST_ZONE}/apply`)
      && response.request().method() === 'POST',
  );
  await page.locator('.button_apply_changes').click();
  await expect(page.locator('#modal_apply_changes')).toBeVisible();
  await page.locator('#button_apply_confirm').click();

  const applyResponse = await applyResponsePromise;
  expect(applyResponse.ok()).toBeTruthy();
  await expect(page.locator('#modal_success')).toBeVisible();
  await page.waitForTimeout(2_500);
  await page.waitForLoadState('networkidle');
  await captureStep(page, testInfo, `${projectName}-submitted`);

  const zoneResponse = await request.get(
    `${PDNS_API_URL}/api/v1/servers/localhost/zones/${TEST_ZONE}.`,
    { headers: pdnsHeaders },
  );
  expect(zoneResponse.ok()).toBeTruthy();
  const zone = await zoneResponse.json();

  for (const record of records) {
    const expectedName = `${record.name}.${TEST_ZONE}.`.toLowerCase();
    const rrset = zone.rrsets.find(
      (candidate) => candidate.name.toLowerCase() === expectedName
        && candidate.type === record.type,
    );
    expect(rrset, `${record.name} should have been submitted`).toBeTruthy();
    expect(rrset.records.some((candidate) => candidate.disabled === false)).toBeTruthy();
  }

  expect(failures, failures.join('\n')).toEqual([]);
});

test('operator cannot promote users or operators to Administrator', async ({
  browser,
  consoleAudit,
  playwright,
}, testInfo) => {
  test.setTimeout(90_000);
  const operatorContext = await browser.newContext({
    baseURL: process.env.BASE_URL || 'http://powerdns-admin',
    colorScheme: testInfo.project.use.colorScheme,
    storageState: {
      cookies: [],
      origins: [],
    },
  });
  await operatorContext.clearCookies();
  const page = await operatorContext.newPage();
  consoleAudit.monitorPage(page);
  consoleAudit.expectMessage(
    'Failed to load resource: the server responded with a status of 400 (BAD REQUEST)',
    { type: 'error' },
  );
  const failures = collectBrowserFailures(page);
  const operator = ROLE_SECURITY_USERS.operator;
  const operatorHeaders = basicAuthHeaders(operator.username, operator.password);
  const operatorApi = await playwright.request.newContext({
    baseURL: process.env.BASE_URL || 'http://powerdns-admin',
    extraHTTPHeaders: operatorHeaders,
    storageState: {
      cookies: [],
      origins: [],
    },
  });
  const administrator = await getApiUser(
    operatorApi, ADMIN_USERNAME, operatorHeaders,
  );

  for (const target of ROLE_SECURITY_USERS.targets) {
    const targetUser = await getApiUser(
      operatorApi, target.username, operatorHeaders,
    );

    for (const rolePayload of [
      { role_name: 'Administrator' },
      { role_id: administrator.role.id },
    ]) {
      const response = await operatorApi.put(
        `/api/v1/pdnsadmin/users/${targetUser.id}`,
        {
          headers: operatorHeaders,
          data: rolePayload,
        },
      );
      expect(response.status()).toBe(401);
    }

    await assertApiRole(
      operatorApi, target.username, target.roleName, operatorHeaders,
    );
  }

  await page.goto('/login');
  await page.getByRole('textbox', { name: 'Username' }).fill(operator.username);
  await page.locator('input[name="password"]').fill(operator.password);
  await Promise.all([
    page.waitForURL(/\/dashboard\//, { waitUntil: 'networkidle' }),
    page.getByRole('button', { name: 'Sign In' }).click(),
  ]);

  await page.goto('/admin/manage-user', { waitUntil: 'networkidle' });
  for (const target of ROLE_SECURITY_USERS.targets) {
    const roleSelector = page.locator(`select#${target.username}`);
    await expect(roleSelector).toBeVisible();
    await expect(
      roleSelector.locator('option[value="Administrator"]'),
    ).toHaveCount(0);
  }
  await captureStep(
    page,
    testInfo,
    `${testInfo.project.name}-operator-role-options`,
  );

  for (const target of ROLE_SECURITY_USERS.targets) {
    const roleResponsePromise = page.waitForResponse(
      (response) => response.url().includes('/admin/manage-user')
        && response.request().method() === 'POST',
    );
    await page.locator(`select#${target.username}`).evaluate((select) => {
      const administratorOption = document.createElement('option');
      administratorOption.value = 'Administrator';
      administratorOption.textContent = 'Administrator';
      select.append(administratorOption);
      select.value = 'Administrator';
      select.dispatchEvent(new Event('change', { bubbles: true }));
    });

    const roleResponse = await roleResponsePromise;
    expect(roleResponse.status()).toBe(400);
    await expect(page.locator('#modal_error')).toBeVisible();
    await expect(page.locator('#modal_error .modal-body')).toContainText(
      'promote a user to Administrator',
    );
    await captureStep(
      page,
      testInfo,
      `${testInfo.project.name}-${target.roleName.toLowerCase()}-promotion-blocked`,
    );
    await page.locator('#modal_error .modal-footer .btn-secondary').click();
    await expect(page.locator('#modal_error')).toBeHidden();

    await assertApiRole(
      operatorApi, target.username, target.roleName, operatorHeaders,
    );
    await page.reload({ waitUntil: 'networkidle' });
  }

  await operatorApi.dispose();
  await operatorContext.close();
  expect(failures, failures.join('\n')).toEqual([]);
});
