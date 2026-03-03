import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

import { isTokenExpired } from '@/app/lib/auth';

export function proxy(request: NextRequest) {
  const token = request.cookies.get('access_token')?.value;

  const isAuthPage = request.nextUrl.pathname === '/login';

  if (!token || isTokenExpired(token)) {
    if (isAuthPage) {
      return NextResponse.next();
    }
    const loginUrl = new URL('/login', request.url);
    loginUrl.searchParams.set('callbackUrl', request.nextUrl.pathname);
    return NextResponse.redirect(loginUrl);
  }

  // Authenticated user trying to access login page → redirect to dashboard
  if (isAuthPage) {
    return NextResponse.redirect(new URL('/dashboard', request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/dashboard/:path*', '/login'],
};
