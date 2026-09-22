import { CanActivateFn } from '@angular/router';

/**
 * Placeholder guard. Authentication does not exist yet in Phase 1, so this
 * intentionally allows every navigation — it exists to give routes a
 * stable import (`canActivate: [authGuard]`) that will start enforcing
 * real checks once AuthStore/AuthService are implemented, without callers
 * having to change.
 */
export const authGuard: CanActivateFn = () => true;
