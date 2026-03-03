const baseURL = process.env.PLAYWRIGHT_BASE_URL || 'http://frontend:3000';

/** @type {import('@playwright/test').PlaywrightTestConfig} */
const config = {
  testDir: './tests',
  timeout: 30_000,
  retries: process.env.CI ? 2 : 0,
  use: {
    baseURL,
    trace: 'retain-on-failure',
  },
};

module.exports = config;
