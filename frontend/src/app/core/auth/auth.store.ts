import { Injectable, computed, signal } from '@angular/core';
import { AuthState, AuthUser } from './auth.models';

/**
 * Holds authentication state as signals. Phase 1 never sets a user, so
 * `isAuthenticated` is always false — this exists purely to give
 * `auth.guard.ts` and future login/logout flows a stable place to read
 * from and write to.
 */
@Injectable({ providedIn: 'root' })
export class AuthStore {
  private readonly _user = signal<AuthUser | null>(null);

  readonly user = this._user.asReadonly();
  readonly isAuthenticated = computed(() => this._user() !== null);

  setUser(user: AuthUser | null): void {
    this._user.set(user);
  }

  snapshot(): AuthState {
    return { user: this._user(), isAuthenticated: this.isAuthenticated() };
  }
}
