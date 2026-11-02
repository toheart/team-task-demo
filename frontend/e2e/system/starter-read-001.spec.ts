import { expect, test } from '@playwright/test';
import { declareCase } from '../support/case';

test('STARTER-READ-001 renders data returned by the Go API', async ({ page }) => {
  declareCase({
    id: 'STARTER-READ-001',
    dev: 'UI loads real /api/v1/samples data',
    remote: { path: 'read-only', assertions: 'Same read path when this starter app is deployed' },
  });

  const response = page.waitForResponse((item) => item.url().includes('/api/v1/samples'));
  await page.goto('/');
  expect((await response).ok()).toBe(true);
  await expect(page.getByRole('heading', { name: 'Backend module' })).toBeVisible();
});
