import { ChangeDetectionStrategy, Component, Input } from '@angular/core';

/**
 * Generic "not built yet" page used by feature routes that only need to
 * prove routing/lazy-loading works in Phase 1. Real feature pages replace
 * their usage of this component as they are implemented in later phases.
 */
@Component({
  selector: 'app-placeholder-page',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <section class="placeholder-page">
      <h1>{{ title }}</h1>
      <p>{{ description }}</p>
      <span class="placeholder-page__badge">Coming in a future phase</span>
    </section>
  `,
  styles: [
    `
      .placeholder-page {
        display: flex;
        flex-direction: column;
        gap: 0.75rem;
        padding: 2rem;
        border: 1px dashed var(--color-border, #d0d5dd);
        border-radius: 8px;
        max-width: 640px;
      }
      .placeholder-page__badge {
        align-self: flex-start;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        color: var(--color-muted, #667085);
        background: var(--color-muted-bg, #f2f4f7);
        padding: 0.25rem 0.6rem;
        border-radius: 999px;
      }
    `,
  ],
})
export class PlaceholderPageComponent {
  @Input({ required: true }) title!: string;
  @Input() description = 'This section has not been implemented yet.';
}
