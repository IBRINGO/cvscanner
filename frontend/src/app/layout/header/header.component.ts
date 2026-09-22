import { ChangeDetectionStrategy, Component } from '@angular/core';
import { isLoading } from '../../core/http/loading.interceptor';

@Component({
  selector: 'app-header',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <header class="app-header">
      <span class="app-header__brand">CVScanner</span>
      @if (isLoading()) {
        <span class="app-header__status" role="status">Working</span>
      }
    </header>
  `,
  styles: [
    `
      .app-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        height: 64px;
        padding: 0 var(--space-6);
        border-bottom: 1px solid var(--border-subtle);
        background: var(--surface-raised);
      }
      .app-header__brand {
        font-family: var(--font-display);
        font-weight: 500;
        font-size: var(--text-lg);
        color: var(--ink-primary);
        letter-spacing: -0.01em;
      }
      .app-header__status {
        font-size: var(--text-sm);
        color: var(--accent);
      }
    `,
  ],
})
export class HeaderComponent {
  protected readonly isLoading = isLoading;
}
