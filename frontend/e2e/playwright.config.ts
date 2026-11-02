import { defineConfig, devices } from '@playwright/test';

const environment = process.env.E2E_ENV ?? 'dev';
if (environment !== 'dev' && environment !== 'remote') {
  throw new Error(`Unsupported E2E_ENV: ${environment}`);
}

const baseURL = environment === 'dev'
  ? 'http://localhost:3000'
  : process.env.E2E_REMOTE_BASE_URL;

if (!baseURL) {
  throw new Error('E2E_REMOTE_BASE_URL is required for remote system tests');
}

export default defineConfig({
  testDir: './system',
  fullyParallel: false,
  forbidOnly: true,
  retries: 0,
  workers: 1,
  timeout: 60_000,
  expect: { timeout: 10_000 },
  metadata: { environment },
  outputDir: './artifacts/system/test-results',
  reporter: [
    ['list'],
    ['html', { open: 'never', outputFolder: 'artifacts/system/report' }],
    ['./support/result-reporter.ts'],
  ],
  use: {
    baseURL,
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  projects: [{ name: `chromium-system-${environment}`, use: { ...devices['Desktop Chrome'] } }],
});
