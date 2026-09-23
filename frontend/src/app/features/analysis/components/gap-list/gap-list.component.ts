import { ChangeDetectionStrategy, Component, Input } from '@angular/core';
import { NgIcon, provideIcons } from '@ng-icons/core';
import { CVSCANNER_ICONS } from '../../../../core/icons';
import { formatEnumLabel } from '../../../../shared/utils/format-label';
import { Gap } from '../../models/analysis.model';

/**
 * The gap section (Phase 4 section 49) - deliberately composed like an
 * editorial list, not an error log. No recommendations here (section 24
 * defers those to Phase 5); each entry only explains what is missing or
 * partial, and why it matters.
 */
@Component({
  selector: 'app-gap-list',
  standalone: true,
  imports: [NgIcon],
  viewProviders: [provideIcons(CVSCANNER_ICONS)],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    @if (gaps.length === 0) {
      <p class="gap-list__empty text-secondary">
        <ng-icon name="lucideClipboardCheck" size="16" />
        No gaps identified - every requirement has at least partial evidence.
      </p>
    } @else {
      <ul class="gap-list">
        @for (gap of gaps; track $index; let i = $index) {
          <li class="gap-list__item" [attr.data-priority]="gap.priority" [style.animation-delay.ms]="i * 40">
            <div class="gap-list__marker" [attr.aria-label]="formatEnumLabel(gap.priority) + ' priority'"></div>
            <div class="gap-list__body">
              <div class="gap-list__head">
                <span class="gap-list__requirement">{{ gap.raw_text }}</span>
                <span class="gap-list__priority text-tertiary">{{ formatEnumLabel(gap.priority) }}</span>
              </div>
              <p class="gap-list__reason">{{ gap.reason }}</p>
              @if (gap.related_candidate_skills.length > 0) {
                <p class="gap-list__related text-tertiary">
                  Related on the CV: {{ gap.related_candidate_skills.join(', ') }}
                </p>
              }
            </div>
          </li>
        }
      </ul>
    }
  `,
  styles: [
    `
      .gap-list__empty {
        display: inline-flex;
        align-items: center;
        gap: var(--space-2);
        margin: 0;
      }
      .gap-list {
        list-style: none;
        margin: 0;
        padding: 0;
        display: flex;
        flex-direction: column;
        gap: var(--space-4);
      }
      .gap-list__item {
        display: grid;
        grid-template-columns: 4px 1fr;
        gap: var(--space-3);
        animation: gap-item-in var(--motion-slow) var(--motion-ease) both;
      }
      .gap-list__marker {
        border-radius: var(--radius-sm);
        background: var(--match-neutral);
      }
      @keyframes gap-item-in {
        from {
          opacity: 0;
          transform: translateY(8px);
        }
        to {
          opacity: 1;
          transform: translateY(0);
        }
      }
      @media (prefers-reduced-motion: reduce) {
        .gap-list__item {
          animation: none;
        }
      }
      .gap-list__item[data-priority='MANDATORY'] .gap-list__marker {
        background: var(--match-negative);
      }
      .gap-list__item[data-priority='PREFERRED'] .gap-list__marker {
        background: var(--match-attention);
      }
      .gap-list__body {
        display: flex;
        flex-direction: column;
        gap: var(--space-1);
      }
      .gap-list__head {
        display: flex;
        align-items: baseline;
        gap: var(--space-3);
        flex-wrap: wrap;
      }
      .gap-list__requirement {
        font-weight: 500;
        color: var(--ink-primary);
      }
      .gap-list__priority {
        font-size: var(--text-xs);
        text-transform: uppercase;
        letter-spacing: 0.04em;
      }
      .gap-list__reason {
        margin: 0;
        color: var(--ink-secondary);
        max-width: 65ch;
      }
      .gap-list__related {
        margin: 0;
        font-size: var(--text-sm);
      }
    `,
  ],
})
export class GapListComponent {
  @Input({ required: true }) gaps!: Gap[];

  formatEnumLabel(value: string): string {
    return formatEnumLabel(value);
  }
}
