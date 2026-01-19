import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  const nonce = Buffer.from(crypto.randomUUID()).toString('base64');

  const scriptSrc = ["'self'", `'nonce-${nonce}'`, "'strict-dynamic'", 'https:'];
  const connectSrc = new Set(["'self'"]);

  const configuredApiUrl = process.env.NEXT_PUBLIC_API_URL ?? 'https://api.valsa.solutions';
  const candidateUrls = [
    configuredApiUrl,
    process.env.NEXT_PUBLIC_WS_URL,
    process.env.NEXT_PUBLIC_INTERNAL_API_URL,
    'https://edustream.valsa.solutions',
    'https://api.valsa.solutions',
    'https://minio.valsa.solutions',
  ].filter((value): value is string => Boolean(value));

  for (const url of candidateUrls) {
    try {
      const origin = new URL(url).origin;
      connectSrc.add(origin);
      
      // Add WebSocket equivalent for HTTPS origins
      if (origin.startsWith('https://')) {
        const wsOrigin = origin.replace('https://', 'wss://');
        connectSrc.add(wsOrigin);
      }
    } catch {
      // Ignore invalid URLs
    }
  }

  const cspHeader = `
    default-src 'self';
    script-src ${scriptSrc.join(' ')};
    connect-src ${Array.from(connectSrc).join(' ')};
    style-src 'self' 'unsafe-inline' https://fonts.googleapis.com;
    img-src 'self' blob: data: https:;
    font-src 'self' https://fonts.gstatic.com;
    object-src 'none';
    base-uri 'self';
    form-action 'self';
    frame-ancestors 'none';
  `.replace(/\s{2,}/g, ' ').trim();

  const requestHeaders = new Headers(request.headers);
  requestHeaders.set('x-nonce', nonce);
  requestHeaders.set('Content-Security-Policy', cspHeader);

  const response = NextResponse.next({
    request: {
      headers: requestHeaders,
    },
  });

  response.headers.set('Content-Security-Policy', cspHeader);
  response.headers.set('X-Content-Type-Options', 'nosniff');
  response.headers.set('X-Frame-Options', 'DENY');
  response.headers.set('X-XSS-Protection', '1; mode=block');
  response.headers.set('Referrer-Policy', 'strict-origin-when-cross-origin');
  response.headers.set('Permissions-Policy', 'camera=(), microphone=(), geolocation=()');

  return response;
}

export const config = {
  matcher: [
    '/((?!api|_next/static|_next/image|favicon.ico|icon.svg|apple-icon.svg).*)',
  ],
};
