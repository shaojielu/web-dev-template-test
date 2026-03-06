import { NextRequest, NextResponse } from 'next/server';
import { isTokenExpired } from '@/app/lib/auth';

const API_BASE_URL =
  process.env.API_BASE_URL ||
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  'http://localhost:8000';

function resolveUrl(path: string) {
  return `${API_BASE_URL.replace(/\/$/, '')}${path.startsWith('/') ? '' : '/'}${path}`;
}

export async function middleware(request: NextRequest) {
  const accessToken = request.cookies.get('access_token')?.value;
  const refreshToken = request.cookies.get('refresh_token')?.value;
  const loginUrl = new URL('/login', request.url);
  loginUrl.searchParams.set('callbackUrl', request.nextUrl.pathname);

  // If access token exists and is valid, continue
  if (accessToken && !isTokenExpired(accessToken)) {
    return NextResponse.next();
  }

  // Access token missing or expired — try to refresh
  if (refreshToken) {
    try {
      const response = await fetch(resolveUrl('/api/v1/login/refresh'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refreshToken }),
        cache: 'no-store',
      });

      if (response.ok) {
        const data = (await response.json()) as {
          access_token?: string;
          refresh_token?: string;
        };

        if (data.access_token) {
          const res = NextResponse.next();
          res.cookies.set('access_token', data.access_token, {
            httpOnly: true,
            sameSite: 'strict',
            path: '/',
          });
          if (data.refresh_token) {
            res.cookies.set('refresh_token', data.refresh_token, {
              httpOnly: true,
              sameSite: 'strict',
              path: '/',
              maxAge: 60 * 60 * 24 * 7,
            });
          }
          return res;
        }
      }
    } catch {
      // Refresh failed, fall through to redirect
    }
  }

  // No valid tokens — redirect to login
  return NextResponse.redirect(loginUrl);
}

export const config = {
  matcher: ['/dashboard/:path*'],
};
