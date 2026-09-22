import { ChangeDetectionStrategy, Component } from '@angular/core';

@Component({
  selector: 'app-footer',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <footer class="app-footer">
      <span>CVScanner — Phase 1 foundation</span>
    </footer>
  `,
  styles: [
    `
      .app-footer {
        padding: 0.75rem 1.5rem;
        border-top: 1px solid var(--color-border, #d0d5dd);
        font-size: 0.8rem;
        color: var(--color-muted, #667085);
      }
    `,
  ],
})
export class FooterComponent {}
