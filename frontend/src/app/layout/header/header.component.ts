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
        <span class="app-header__status" role="status">Loading…</span>
      }
    </header>
  `,
  styles: [
    `
      .app-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0.75rem 1.5rem;
        border-bottom: 1px solid var(--color-border, #d0d5dd);
      }
      .app-header__brand {
        font-weight: 600;
        font-size: 1.1rem;
      }
      .app-header__status {
        font-size: 0.85rem;
        color: var(--color-muted, #667085);
      }
    `,
  ],
})
export class HeaderComponent {
  protected readonly isLoading = isLoading;
}
