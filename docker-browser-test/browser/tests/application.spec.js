const { test, expect } = require('@playwright/test');

function collectBrowserFailures(page) {
  const failures = [];

  page.on('pageerror', (error) => failures.push(`pageerror: ${error.message}`));
  page.on('console', (message) => {
    if (message.type() === 'error') {
      failures.push(`console: ${message.text()}`);
    }
  });
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

test('TXT helper closes once and unsaved banner remains reachable', async ({ page }) => {
  const failures = collectBrowserFailures(page);
  await page.goto('/domain/browser-test.example', { waitUntil: 'networkidle' });

  await page.getByRole('button', { name: /Add Record/i }).click();
  const row = page.locator('#tbl_records tbody tr').last();
  await row.locator('#record_type').selectOption('TXT');
  await row.locator('#current_edit_record_data').click();

  const helper = page.locator('#modal_custom_record');
  await expect(helper).toBeVisible();
  await helper.locator('textarea').fill('automated browser check');
  await helper.getByRole('button', { name: /Save/i }).click();
  await expect(helper).toBeHidden();
  await page.waitForTimeout(500);
  await expect(helper).toBeHidden();

  await row.locator('.button_save').click();
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

  expect(failures, failures.join('\n')).toEqual([]);
});
