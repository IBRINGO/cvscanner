import { Injectable } from '@angular/core';
import { Observable, throwError } from 'rxjs';
import { AuthStore } from './auth.store';

/**
 * Not implemented in Phase 1. Login/logout will call the future
 * `/api/v1/auth/` endpoints once they exist; for now every method fails
 * loudly instead of pretending to authenticate, so nothing in the app can
 * silently rely on a fake session.
 */
@Injectable({ providedIn: 'root' })
export class AuthService {
  constructor(private readonly authStore: AuthStore) {}

  login(_email: string, _password: string): Observable<never> {
    return throwError(() => new Error('Authentication is not implemented yet (planned for a later phase).'));
  }

  logout(): void {
    this.authStore.setUser(null);
  }
}
