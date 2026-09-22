import { HttpInterceptorFn } from '@angular/common/http';

/**
 * Placeholder for attaching an auth token to outgoing requests.
 * Authentication is not implemented in Phase 1 (see core/auth) — this
 * interceptor currently passes every request through unchanged so the
 * HTTP pipeline shape (core/http) doesn't need to change once auth lands.
 */
export const authInterceptor: HttpInterceptorFn = (req, next) => {
  return next(req);
};
