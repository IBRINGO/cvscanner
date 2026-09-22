import { ChangeDetectionStrategy, Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';

/**
 * Minimal centered shell for future unauthenticated pages (login, signup,
 * password reset). Not wired to any route yet since Phase 1 has no auth
 * pages — kept here so `core/auth` has a layout to render into once it
 * does.
 */
@Component({
  selector: 'app-auth-layout',
  standalone: true,
  imports: [RouterOutlet],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="auth-shell">
      <router-outlet />
    </div>
  `,
  styles: [
    `
      .auth-shell {
        display: flex;
        align-items: center;
        justify-content: center;
        min-height: 100vh;
      }
    `,
  ],
})
export class AuthLayoutComponent {}
