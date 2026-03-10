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

async function refreshAccessToken(): Promise<string | null> {
  const cookieStore = await cookies();
  const refreshToken = cookieStore.get('refresh_token')?.value;
  if (!refreshToken) {
    return null;
  }

  try {
    const response = await fetch(resolveUrl('/api/v1/login/refresh'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken }),
      cache: 'no-store',
    });

    if (!response.ok) {
      return null;
    }

    const data = (await response.json()) as {
      access_token?: string;
      refresh_token?: string;
    };
    if (!data.access_token) {
      return null;
    }

    cookieStore.set('access_token', data.access_token, {
      httpOnly: true,
      sameSite: 'strict',
      path: '/',
    });
    if (data.refresh_token) {
      cookieStore.set('refresh_token', data.refresh_token, {
        httpOnly: true,
        sameSite: 'strict',
        path: '/',
        maxAge: 60 * 60 * 24 * 7,
      });
    }

    return data.access_token;
  } catch {
    return null;
  }
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

  let response = await fetch(resolveUrl(path), nextOptions);

  if (response.status === 401 && auth !== false) {
    const newToken = await refreshAccessToken();
    if (newToken) {
      headers.set('Authorization', `Bearer ${newToken}`);
      const retryOptions: RequestInit & { next?: { revalidate?: number | false } } = {
        ...fetchOptions,
        headers,
      };
      if (revalidate !== undefined) {
        retryOptions.next = { revalidate };
      } else {
        retryOptions.cache = 'no-store';
      }
      response = await fetch(resolveUrl(path), retryOptions);
    }
  }

  if (!response.ok) {
    if (response.status === 401) {
      redirect('/login');
    }
    let message = `Request failed with ${response.status}`;
    try {
      const body = await response.json();
      if (typeof body.detail === 'string') {
        message = body.detail;
      }
    } catch {
      // response was not JSON, use generic message
    }
    throw new ApiError(response.status, message);
  }

  if (response.status === 204) {
    return undefined as unknown as T;
  }

  return (await response.json()) as T;
}
