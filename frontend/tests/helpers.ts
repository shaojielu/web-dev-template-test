import fs from 'node:fs';
import path from 'node:path';
import type { Page } from '@playwright/test';
import { expect } from '@playwright/test';

type CredentialKeys = 'FIRST_SUPERUSER' | 'FIRST_SUPERUSER_PASSWORD';

function readCredentialsFromEnvFiles(): Partial<Record<CredentialKeys, string>> {
  const keys: CredentialKeys[] = ['FIRST_SUPERUSER', 'FIRST_SUPERUSER_PASSWORD'];
  const credentials: Partial<Record<CredentialKeys, string>> = {};
  const envFilePaths = [
    path.resolve(process.cwd(), '.env'),
    path.resolve(process.cwd(), '../.env'),
  ];

  for (const envFilePath of envFilePaths) {
    if (!fs.existsSync(envFilePath)) {
      continue;
    }

    const content = fs.readFileSync(envFilePath, 'utf8');
    const lines = content.split(/\r?\n/);

    for (const rawLine of lines) {
      const line = rawLine.trim();
      if (!line || line.startsWith('#')) {
        continue;
      }

      const separatorIndex = line.indexOf('=');
      if (separatorIndex <= 0) {
        continue;
      }

      const key = line.slice(0, separatorIndex).trim() as CredentialKeys;
      if (!keys.includes(key)) {
        continue;
      }

      let value = line.slice(separatorIndex + 1).trim();
      if (
        (value.startsWith('"') && value.endsWith('"')) ||
        (value.startsWith("'") && value.endsWith("'"))
      ) {
        value = value.slice(1, -1);
      }

      credentials[key] = value;
    }
  }

  return credentials;
}

const envFileCredentials = readCredentialsFromEnvFiles();

export const userEmail =
  process.env.FIRST_SUPERUSER ||
  envFileCredentials.FIRST_SUPERUSER ||
  'admin@example.com';

export const userPassword =
  process.env.FIRST_SUPERUSER_PASSWORD ||
  envFileCredentials.FIRST_SUPERUSER_PASSWORD ||
  'aabbcc123456789';

export async function login(page: Page) {
  await page.goto('/login');
  await page.getByLabel('Email').fill(userEmail);
  await page.getByLabel('Password').fill(userPassword);
  await page.getByTestId('login-submit-button').click();
  await expect(page).toHaveURL((url) => url.pathname === '/dashboard');
}
