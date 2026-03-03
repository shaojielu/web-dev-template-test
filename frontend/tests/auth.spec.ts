import { expect, test } from '@playwright/test';

import { login, userEmail } from './helpers';

test('login page is reachable', async ({ page }) => {
  await page.goto('/login');
  await expect(page).toHaveURL(/\/login$/);
});

test('user can login and view dashboard', async ({ page }) => {
  await login(page);
  await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
});

test('invalid credentials show error message', async ({ page }) => {
  await page.goto('/login');
  await page.getByLabel('Email').fill(userEmail);
  await page.getByLabel('Password').fill('invalid-password');
  await page.getByTestId('login-submit-button').click();
  await expect(page.getByText('Incorrect email or password.')).toBeVisible();
  await expect(page).toHaveURL(/\/login$/);
});

test('expired session redirects back to login', async ({ page, context, baseURL }) => {
  if (!baseURL) {
    throw new Error('baseURL is required for cookie-based test.');
  }
  await context.addCookies([
    {
      name: 'access_token',
      value: 'invalid.token.value',
      url: baseURL,
      path: '/',
    },
  ]);
  await page.goto('/dashboard');
  await expect(page).toHaveURL(/\/login/);
});
