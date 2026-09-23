import { ChangeDetectionStrategy, Component, Input, signal } from '@angular/core';
import { NgIcon, provideIcons } from '@ng-icons/core';
import { CVSCANNER_ICONS } from '../../../../core/icons';
import { formatEnumLabel } from '../../../../shared/utils/format-label';
import { MatchSignalBadgeComponent } from '../match-signal-badge/match-signal-badge.component';
import { RequirementEvaluation } from '../../models/analysis.model';

const PRIORITY_ICON: Record<string, string> = {
  MANDATORY: 'lucideTarget',
  PREFERRED: 'lucideCircleCheck',
  OPTIONAL: 'lucideMinus',
};

const SIGNAL_TONE: Record<string, 'positive' | 'attention' | 'negative' | 'semantic'> = {
  EXACT_MATCH: 'positive',
  ALIAS_MATCH: 'positive',
  RELATED_MATCH: 'attention',
  SEMANTIC_MATCH: 'semantic',
  PARTIAL_MATCH: 'attention',
  NO_EVIDENCE: 'negative',
};

/**
 * The requirement matrix (Phase 4 section 46) - the central component of
 * the analysis workspace. Each row answers "what was required, what do I
 * have, how strong is the match, why" (section 46); expanding a row
 * reveals the evidence explorer for that one requirement (section 47),
 * with a subtle motion respecting prefers-reduced-motion (section 52).
 */
@Component({
  selector: 'app-requirement-matrix',
  standalone: true,
  imports: [NgIcon, MatchSignalBadgeComponent],
  viewProviders: [provideIcons(CVSCANNER_ICONS)],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <ul class="requirement-matrix">
      @for (evaluation of evaluations; track $index; let i = $index) {
        <li
          class="requirement-matrix__row"
          [attr.data-tone]="matchTone(evaluation.match_signal)"
          [style.animation-delay.ms]="i * 30"
        >
          <button
            type="button"
            class="requirement-matrix__summary"
            [attr.aria-expanded]="isExpanded($index)"
            (click)="toggle($index)"
          >
            <ng-icon
              class="requirement-matrix__priority-icon"
              [name]="priorityIcon(evaluation.priority)"
              size="16"
              [attr.aria-label]="formatEnumLabel(evaluation.priority) + ' requirement'"
            />
            <span class="requirement-matrix__text">
              {{ evaluation.raw_text }}
              @if (evaluation.matched_skill && evaluation.matched_skill !== evaluation.raw_text) {
                <span class="text-tertiary font-mono"> (via {{ evaluation.matched_skill }})</span>
              }
            </span>
            <span class="requirement-matrix__priority text-tertiary">{{ formatEnumLabel(evaluation.priority) }}</span>
            <app-match-signal-badge [signal]="evaluation.match_signal" />
            <ng-icon
              class="requirement-matrix__chevron"
              [name]="isExpanded($index) ? 'lucideChevronDown' : 'lucideChevronRight'"
              size="16"
            />
          </button>

          @if (isExpanded($index)) {
            <div class="requirement-matrix__detail">
              <p class="requirement-matrix__explanation">{{ evaluation.explanation }}</p>
              <p class="requirement-matrix__confidence text-tertiary font-mono">
                Confidence: {{ confidenceLabel(evaluation.confidence) }}
              </p>
              @if (evaluation.evidence.length > 0) {
                <ul class="requirement-matrix__evidence-list">
                  @for (item of evaluation.evidence; track $index) {
                    <li class="requirement-matrix__evidence">
                      <figure class="evidence-figure">
                        <figcaption class="text-tertiary font-mono">
                          {{ item.source_label ?? formatEnumLabel(item.source_type) }}
                          @if (item.page_number) {
                            <span> - Page {{ item.page_number }}</span>
                          }
                        </figcaption>
                        <blockquote>{{ item.text }}</blockquote>
                      </figure>
                    </li>
                  }
                </ul>
              } @else {
                <p class="requirement-matrix__no-evidence text-tertiary">
                  <ng-icon name="lucideCircleHelp" size="14" />
                  No source text is attached to this evaluation.
                </p>
              }
            </div>
          }
        </li>
      }
    </ul>
  `,
  styles: [
    `
      .requirement-matrix {
        list-style: none;
        margin: 0;
        padding: 0;
        border-top: 1px solid var(--border-subtle);
      }
      .requirement-matrix__row {
        border-bottom: 1px solid var(--border-subtle);
        border-left: 3px solid transparent;
        animation: requirement-row-in var(--motion-slow) var(--motion-ease) both;
      }
      .requirement-matrix__row[data-tone='positive'] {
        border-left-color: var(--match-positive);
      }
      .requirement-matrix__row[data-tone='attention'] {
        border-left-color: var(--match-attention);
      }
      .requirement-matrix__row[data-tone='negative'] {
        border-left-color: var(--match-negative);
      }
      .requirement-matrix__row[data-tone='semantic'] {
        border-left-color: var(--match-semantic);
      }
      .requirement-matrix__summary {
        width: 100%;
        display: grid;
        grid-template-columns: 20px 1fr auto auto 16px;
        align-items: center;
        gap: var(--space-3);
        padding: var(--space-3) var(--space-3);
        background: none;
        border: none;
        font: inherit;
        text-align: left;
        cursor: pointer;
        color: var(--ink-primary);
        transition: background var(--motion-fast) var(--motion-ease);
      }
      .requirement-matrix__summary:hover {
        background: var(--surface-sunken);
      }

      @keyframes requirement-row-in {
        from {
          opacity: 0;
          transform: translateX(-6px);
        }
        to {
          opacity: 1;
          transform: translateX(0);
        }
      }
      .requirement-matrix__priority-icon {
        color: var(--ink-tertiary);
      }
      .requirement-matrix__text {
        font-weight: 500;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }
      .requirement-matrix__priority {
        font-size: var(--text-xs);
        text-transform: uppercase;
        letter-spacing: 0.04em;
      }
      .requirement-matrix__chevron {
        color: var(--ink-tertiary);
      }
      .requirement-matrix__detail {
        padding: 0 var(--space-1) var(--space-4) calc(20px + var(--space-3) + var(--space-1));
        display: flex;
        flex-direction: column;
        gap: var(--space-3);
        animation: requirement-detail-in var(--motion-base) var(--motion-ease);
      }
      .requirement-matrix__explanation {
        margin: 0;
        color: var(--ink-secondary);
        max-width: 65ch;
      }
      .requirement-matrix__confidence {
        margin: 0;
        font-size: var(--text-xs);
      }
      .requirement-matrix__evidence-list {
        list-style: none;
        margin: 0;
        padding: 0;
        display: flex;
        flex-direction: column;
        gap: var(--space-2);
      }
      .evidence-figure {
        margin: 0;
        padding-left: var(--space-3);
        border-left: 2px solid var(--border-subtle);
      }
      .evidence-figure figcaption {
        font-size: var(--text-xs);
        margin-bottom: 2px;
      }
      .evidence-figure blockquote {
        margin: 0;
        font-size: var(--text-sm);
        font-style: italic;
        color: var(--ink-secondary);
      }
      .requirement-matrix__no-evidence {
        display: inline-flex;
        align-items: center;
        gap: var(--space-1);
        font-size: var(--text-sm);
        margin: 0;
      }
      @keyframes requirement-detail-in {
        from {
          opacity: 0;
          transform: translateY(-4px);
        }
        to {
          opacity: 1;
          transform: translateY(0);
        }
      }
      @media (prefers-reduced-motion: reduce) {
        .requirement-matrix__detail {
          animation: none;
        }
        .requirement-matrix__row {
          animation: none;
        }
        .requirement-matrix__summary {
          transition: none;
        }
      }
      @media (max-width: 640px) {
        .requirement-matrix__summary {
          grid-template-columns: 20px 1fr 16px;
          grid-template-rows: auto auto;
        }
        .requirement-matrix__priority-icon {
          grid-column: 1;
          grid-row: 1;
        }
        .requirement-matrix__priority {
          display: none;
        }
        .requirement-matrix__summary app-match-signal-badge {
          grid-column: 2 / 3;
          grid-row: 2;
          justify-self: start;
        }
        .requirement-matrix__text {
          grid-column: 2;
          grid-row: 1;
          white-space: normal;
        }
        .requirement-matrix__chevron {
          grid-column: 3;
          grid-row: 1;
        }
      }
    `,
  ],
})
export class RequirementMatrixComponent {
  @Input({ required: true }) evaluations!: RequirementEvaluation[];

  private readonly expandedIndexes = signal<Set<number>>(new Set());

  isExpanded(index: number): boolean {
    return this.expandedIndexes().has(index);
  }

  toggle(index: number): void {
    this.expandedIndexes.update((current) => {
      const next = new Set(current);
      if (next.has(index)) {
        next.delete(index);
      } else {
        next.add(index);
      }
      return next;
    });
  }

  priorityIcon(priority: string): string {
    return PRIORITY_ICON[priority] ?? 'lucideMinus';
  }

  matchTone(signal: string): string {
    return SIGNAL_TONE[signal] ?? 'attention';
  }

  confidenceLabel(confidence: number): string {
    if (confidence >= 0.75) return 'High';
    if (confidence >= 0.4) return 'Medium';
    return 'Low';
  }

  formatEnumLabel(value: string): string {
    return formatEnumLabel(value);
  }
}
