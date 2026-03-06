import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

import { isTokenExpired } from '@/app/lib/auth';

const API_BASE_URL =
  process.env.API_BASE_URL ||
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  'http://localhost:8000';

function resolveUrl(path: string) {
  return `${API_BASE_URL.replace(/\/$/, '')}${path.startsWith('/') ? '' : '/'}${path}`;
}

async function tryRefresh(
  refreshToken: string,
): Promise<{ access_token: string; refresh_token?: string } | null> {
  try {
    const response = await fetch(resolveUrl('/api/v1/login/refresh'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken }),
      cache: 'no-store',
    });

    if (!response.ok) return null;

    const data = (await response.json()) as {
      access_token?: string;
      refresh_token?: string;
    };
    if (!data.access_token) return null;

    return { access_token: data.access_token, refresh_token: data.refresh_token };
  } catch {
    return null;
  }
}

function setTokenCookies(
  res: NextResponse,
  tokens: { access_token: string; refresh_token?: string },
) {
  res.cookies.set('access_token', tokens.access_token, {
    httpOnly: true,
    sameSite: 'strict',
    path: '/',
  });
  if (tokens.refresh_token) {
    res.cookies.set('refresh_token', tokens.refresh_token, {
      httpOnly: true,
      sameSite: 'strict',
      path: '/',
      maxAge: 60 * 60 * 24 * 7,
    });
  }
}

export async function proxy(request: NextRequest) {
  const accessToken = request.cookies.get('access_token')?.value;
  const refreshToken = request.cookies.get('refresh_token')?.value;
  const isAuthPage = request.nextUrl.pathname === '/login';

  const hasValidAccess = accessToken && !isTokenExpired(accessToken);

  // Valid access token — redirect away from login page, or continue
  if (hasValidAccess) {
    if (isAuthPage) {
      return NextResponse.redirect(new URL('/dashboard', request.url));
    }
    return NextResponse.next();
  }

  // Access token missing/expired — try silent refresh
  if (refreshToken) {
    const tokens = await tryRefresh(refreshToken);
    if (tokens) {
      if (isAuthPage) {
        const res = NextResponse.redirect(new URL('/dashboard', request.url));
        setTokenCookies(res, tokens);
        return res;
      }
      const res = NextResponse.next();
      setTokenCookies(res, tokens);
      return res;
    }
  }

  // No valid tokens — allow login page, redirect everything else
  if (isAuthPage) {
    return NextResponse.next();
  }
  const loginUrl = new URL('/login', request.url);
  loginUrl.searchParams.set('callbackUrl', request.nextUrl.pathname);
  return NextResponse.redirect(loginUrl);
}

export const config = {
  matcher: ['/dashboard/:path*', '/login'],
};
