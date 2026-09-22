import { ChangeDetectionStrategy, Component, Input } from '@angular/core';
import { NgIcon, provideIcons } from '@ng-icons/core';
import { CVSCANNER_ICONS } from '../../../../core/icons';

/**
 * A small labelled tag with an optional icon - the single reusable
 * primitive for every normalized/derived value shown in the product
 * (seniority, degree level, language proficiency, employment type, ...).
 * Section 54: one shared shape/spacing/icon language instead of each
 * feature hand-rolling its own tag markup.
 */
@Component({
  selector: 'app-entity-tag',
  standalone: true,
  imports: [NgIcon],
  viewProviders: [provideIcons(CVSCANNER_ICONS)],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <span class="entity-tag">
      @if (icon) {
        <ng-icon [name]="icon" size="12" />
      }
      {{ label }}
    </span>
  `,
  styles: [
    `
      .entity-tag {
        display: inline-flex;
        align-items: center;
        gap: var(--space-1);
        font-size: var(--text-xs);
        text-transform: uppercase;
        letter-spacing: 0.04em;
        color: var(--ink-tertiary);
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-sm);
        padding: 2px var(--space-2);
      }
    `,
  ],
})
export class EntityTagComponent {
  @Input({ required: true }) label!: string;
  @Input() icon: string | null = null;
}
