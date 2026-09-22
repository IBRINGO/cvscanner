import { ChangeDetectionStrategy, Component } from '@angular/core';

@Component({
  selector: 'app-footer',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <footer class="app-footer">
      <span>CVScanner</span>
    </footer>
  `,
  styles: [
    `
      .app-footer {
        padding: var(--space-3) var(--space-6);
        border-top: 1px solid var(--border-subtle);
        font-size: var(--text-xs);
        color: var(--ink-tertiary);
      }
    `,
  ],
})
export class FooterComponent {}
