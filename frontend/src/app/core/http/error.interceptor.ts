import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { catchError, throwError } from 'rxjs';
import { NotificationService } from '../services/notification.service';

/**
 * Normalizes HTTP errors into a single shape and surfaces a notification.
 * Feature code still receives the error via the returned observable so it
 * can react (e.g. show a field-level validation message); this interceptor
 * only handles the cross-cutting "something went wrong" concern.
 */
export const errorInterceptor: HttpInterceptorFn = (req, next) => {
  const notifications = inject(NotificationService);

  return next(req).pipe(
    catchError((error: unknown) => {
      if (error instanceof HttpErrorResponse) {
        const message = error.error?.detail ?? error.message ?? 'Request failed';

        if (error.status === 0) {
          notifications.error('Unable to reach the server. Check your connection.');
        } else if (error.status >= 500) {
          notifications.error('The server encountered an error. Please try again.');
        } else {
          notifications.error(message);
        }
      }

      return throwError(() => error);
    }),
  );
};
