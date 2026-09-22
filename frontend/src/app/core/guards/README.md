# core/guards

Reserved for route guards that are not authentication-specific (e.g. a
future feature-flag guard or an unsaved-changes confirmation guard).

The current authentication guard lives in
[`core/auth/auth.guard.ts`](../auth/auth.guard.ts) since it is tightly
coupled to `AuthStore`. Move it here only if/when it needs to compose with
other guards defined in this folder.
