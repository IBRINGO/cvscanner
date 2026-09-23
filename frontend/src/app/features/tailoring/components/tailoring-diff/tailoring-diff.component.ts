import { ChangeDetectionStrategy, Component, Input } from '@angular/core';
import { NgIcon, provideIcons } from '@ng-icons/core';
import { CVSCANNER_ICONS } from '../../../../core/icons';
import { DiffSegment, TailoringChange } from '../../models/tailoring.model';

/**
 * One tailored change, shown as an editorial before/after with inline
 * diff highlighting (Phase 5 sections 29, 48, 57). A rejected change is
 * never hidden - it is shown with the reason it was rejected, so the
 * candidate always sees why the original text was kept (section 57:
 * explain, don't hide).
 */
@Component({
  selector: 'app-tailoring-diff',
  standalone: true,
  imports: [NgIcon],
  viewProviders: [provideIcons(CVSCANNER_ICONS)],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <article class="tailoring-diff" [attr.data-accepted]="change.accepted">
      <header class="tailoring-diff__header">
        <span class="tailoring-diff__title">{{ change.recommendation_title }}</span>
        @if (change.accepted) {
          <span class="tailoring-diff__status tailoring-diff__status--accepted">
            <ng-icon name="lucideCircleCheck" size="14" />
            Applied
          </span>
        } @else {
          <span class="tailoring-diff__status tailoring-diff__status--rejected">
            <ng-icon name="lucideCircleX" size="14" />
            Not applied
          </span>
        }
      </header>

      @if (change.accepted && hasVisibleChange()) {
        <p class="tailoring-diff__text">
          @for (segment of change.diff; track $index) {
            <span [attr.data-change]="segment.change_type">{{ segment.text }}</span>
            @if (!$last) {
              {{ ' ' }}
            }
          }
        </p>
      } @else {
        <p class="tailoring-diff__text tailoring-diff__text--unchanged">{{ change.original_text }}</p>
      }

      @if (!change.accepted && change.rejection_reasons.length > 0) {
        <p class="tailoring-diff__rejection">
          <ng-icon name="lucideTriangleAlert" size="14" />
          The generated wording could not be verified against your CV
          ({{ formatReasons() }}) and was rejected automatically.
        </p>
      }
    </article>
  `,
  styles: [
    `
      .tailoring-diff {
        display: flex;
        flex-direction: column;
        gap: var(--space-2);
        padding: var(--space-4) var(--space-5);
        margin-bottom: var(--space-3);
        background: var(--paper-surface);
        border: 1px solid var(--paper-border);
        border-radius: var(--radius-sm);
        box-shadow: var(--shadow-document);
        color: var(--paper-ink);
      }
      .tailoring-diff__header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: var(--space-3);
      }
      .tailoring-diff__title {
        font-weight: 500;
      }
      .tailoring-diff__status {
        display: inline-flex;
        align-items: center;
        gap: var(--space-1);
        font-size: var(--text-xs);
        font-weight: 500;
        white-space: nowrap;
      }
      .tailoring-diff__status--accepted {
        color: var(--match-positive);
      }
      .tailoring-diff__status--rejected {
        color: var(--match-neutral);
      }
      .tailoring-diff__text {
        margin: 0;
        max-width: 65ch;
        line-height: 1.6;
      }
      .tailoring-diff__text--unchanged {
        color: var(--paper-ink-secondary);
      }
      .tailoring-diff__text span[data-change='ADDED'] {
        background: var(--match-positive-tint);
        color: var(--match-positive);
        border-radius: 2px;
        padding: 0 2px;
      }
      .tailoring-diff__text span[data-change='REMOVED'] {
        color: var(--paper-ink-secondary);
        text-decoration: line-through;
      }
      .tailoring-diff__rejection {
        display: flex;
        align-items: flex-start;
        gap: var(--space-2);
        margin: 0;
        font-size: var(--text-sm);
        max-width: 65ch;
        color: var(--paper-ink-secondary);
      }
    `,
  ],
})
export class TailoringDiffComponent {
  @Input({ required: true }) change!: TailoringChange;

  hasVisibleChange(): boolean {
    return this.change.diff.some((segment: DiffSegment) => segment.change_type !== 'UNCHANGED');
  }

  formatReasons(): string {
    return this.change.rejection_reasons
      .map((reason) => reason.toLowerCase().replace(/_/g, ' '))
      .join(', ');
  }
}
