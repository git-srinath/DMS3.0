import { NextResponse } from 'next/server';

export function middleware(request) {
  const path = request.nextUrl.pathname;
  const token = request.cookies.get('token')?.value || '';
  
  // Define public and protected paths
  const isAuthPath = path.startsWith('/auth');
  const isChangePasswordPath = path === '/auth/change-password';
  const isPublicPath = isAuthPath && !isChangePasswordPath;
  
  // If user is not authenticated and trying to access a protected route, redirect to login
  if (!token && !isPublicPath) {
    return NextResponse.redirect(new URL('/auth/login', request.url));
  }
  
  // If user is authenticated and trying to access auth routes (except change-password), redirect to home
  if (token && isAuthPath && !isChangePasswordPath) {
    return NextResponse.redirect(new URL('/home', request.url));
  }
  
  return NextResponse.next();
}

// Configure middleware to run on specific paths
export const config = {
  matcher: ['/((?!api|_next/static|_next/image|favicon.ico|.*\\.png$).*)'],
}; 