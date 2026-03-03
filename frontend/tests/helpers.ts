import type { Page } from '@playwright/test';
import { expect } from '@playwright/test';

export const userEmail = process.env.FIRST_SUPERUSER || 'admin@example.com';
export const userPassword = process.env.FIRST_SUPERUSER_PASSWORD || 'changethis';

export async function login(page: Page) {
  await page.goto('/login');
  await page.getByLabel('Email').fill(userEmail);
  await page.getByLabel('Password').fill(userPassword);
  await page.getByTestId('login-submit-button').click();
  await expect(page).toHaveURL(/\/dashboard$/);
}
