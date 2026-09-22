/**
 * Shape of the future authenticated user. Not populated by anything yet —
 * authentication is out of scope for Phase 1.
 */
export interface AuthUser {
  id: string;
  email: string;
  displayName: string;
}

export interface AuthState {
  user: AuthUser | null;
  isAuthenticated: boolean;
}
