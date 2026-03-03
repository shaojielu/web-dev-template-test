import { expect, test } from '@playwright/test';

import { login } from './helpers';

test('invoice create, update and delete flow works', async ({ page }) => {
  await login(page);

  const createdAmount = '1234.56';
  const updatedAmount = '2234.56';

  await page.goto('/dashboard/invoices/create');
  const customerSelect = page.locator('select[name="customerId"]');
  await expect(customerSelect).toBeVisible();
  await customerSelect.selectOption({ index: 1 });
  await page.locator('input[name="amount"]').fill(createdAmount);
  await page.locator('input#paid').check();
  await page.getByRole('button', { name: 'Create Invoice' }).click();
  await expect(page).toHaveURL(/\/dashboard\/invoices$/);

  const searchInput = page.getByTestId('invoice-search-input');
  await searchInput.fill(createdAmount);
  const createdRow = page.locator('tr', { hasText: '$1,234.56' }).first();
  await expect(createdRow).toBeVisible();

  await createdRow.getByTestId('invoice-edit-button').click();
  await expect(page).toHaveURL(/\/dashboard\/invoices\/.+\/edit$/);
  await page.locator('input[name="amount"]').fill(updatedAmount);
  await page.getByRole('button', { name: 'Update Invoice' }).click();
  await expect(page).toHaveURL(/\/dashboard\/invoices$/);

  await searchInput.fill(updatedAmount);
  const updatedRow = page.locator('tr', { hasText: '$2,234.56' }).first();
  await expect(updatedRow).toBeVisible();

  await updatedRow.getByTestId('invoice-delete-button').click();
  await expect(page.locator('tr', { hasText: '$2,234.56' })).toHaveCount(0);
});

test('invoice edit page shows not found for missing invoice', async ({ page }) => {
  await login(page);
  await page.goto('/dashboard/invoices/00000000-0000-0000-0000-000000000000/edit');
  await expect(page.getByText('404 Not Found')).toBeVisible();
});
