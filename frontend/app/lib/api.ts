import 'server-only';

import { cookies } from 'next/headers';
import { redirect } from 'next/navigation';

export const API_BASE_URL =
  process.env.API_BASE_URL ||
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  'http://localhost:8000';

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

function resolveUrl(path: string) {
  if (path.startsWith('http://') || path.startsWith('https://')) {
    return path;
  }
  return `${API_BASE_URL.replace(/\/$/, '')}${path.startsWith('/') ? '' : '/'}${path}`;
}

export async function apiFetch<T>(
  path: string,
  options: RequestInit & { auth?: boolean; revalidate?: number | false } = {},
): Promise<T> {
  const { auth, revalidate, ...fetchOptions } = options;
  const headers = new Headers(fetchOptions.headers);

  if (auth !== false) {
    const cookieStore = await cookies();
    const token = cookieStore.get('access_token')?.value;
    if (token) {
      headers.set('Authorization', `Bearer ${token}`);
    }
  }

  if (fetchOptions.body && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  const nextOptions: RequestInit & { next?: { revalidate?: number | false } } = {
    ...fetchOptions,
    headers,
  };

  if (revalidate !== undefined) {
    nextOptions.next = { revalidate };
  } else {
    nextOptions.cache = 'no-store';
  }

  const response = await fetch(resolveUrl(path), nextOptions);

  if (!response.ok) {
    if (response.status === 401) {
      redirect('/login');
    }
    const message = await response.text();
    throw new ApiError(
      response.status,
      message || `Request failed with ${response.status}`,
    );
  }

  if (response.status === 204) {
    return undefined as unknown as T;
  }

  return (await response.json()) as T;
}
