import { HttpInterceptorFn } from '@angular/common/http';
import { signal } from '@angular/core';
import { finalize } from 'rxjs';

/** Number of HTTP requests currently in flight. */
export const pendingRequestCount = signal(0);

/** True while at least one HTTP request is in flight. */
export const isLoading = signal(false);

/**
 * Tracks in-flight HTTP requests so the shell (e.g. layout/header) can show
 * a global loading indicator without every feature service managing its
 * own loading flag.
 */
export const loadingInterceptor: HttpInterceptorFn = (req, next) => {
  pendingRequestCount.update((count) => count + 1);
  isLoading.set(true);

  return next(req).pipe(
    finalize(() => {
      pendingRequestCount.update((count) => Math.max(0, count - 1));
      isLoading.set(pendingRequestCount() > 0);
    }),
  );
};
