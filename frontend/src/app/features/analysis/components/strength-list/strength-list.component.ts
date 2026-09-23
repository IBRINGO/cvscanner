import { ChangeDetectionStrategy, Component, Input } from '@angular/core';
import { NgIcon, provideIcons } from '@ng-icons/core';
import { CVSCANNER_ICONS } from '../../../../core/icons';
import { RequirementEvaluation } from '../../models/analysis.model';

/**
 * "What is working" - the positive counterpart to the gap list, so a
 * result reads as a story (what's strong, then what needs attention)
 * rather than only a list of problems. Built from the same
 * RequirementEvaluation rows the matrix already renders (status MET),
 * never a separate fabricated summary.
 */
@Component({
  selector: 'app-strength-list',
  standalone: true,
  imports: [NgIcon],
  viewProviders: [provideIcons(CVSCANNER_ICONS)],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    @if (strengths.length === 0) {
      <p class="strength-list__empty text-secondary">
        <ng-icon name="lucideCircleHelp" size="16" />
        No requirements are fully met yet.
      </p>
    } @else {
      <ul class="strength-list">
        @for (item of strengths; track $index) {
          <li class="strength-list__item">
            <ng-icon name="lucideCircleCheck" size="16" class="strength-list__icon" />
            <div class="strength-list__body">
              <span class="strength-list__requirement">
                {{ item.raw_text }}
                @if (item.matched_skill && item.matched_skill !== item.raw_text) {
                  <span class="text-tertiary font-mono"> (via {{ item.matched_skill }})</span>
                }
              </span>
              <p class="strength-list__explanation text-secondary">{{ item.explanation }}</p>
            </div>
          </li>
        }
      </ul>
    }
  `,
  styles: [
    `
      .strength-list__empty {
        display: inline-flex;
        align-items: center;
        gap: var(--space-2);
        margin: 0;
      }
      .strength-list {
        list-style: none;
        margin: 0;
        padding: 0;
        display: flex;
        flex-direction: column;
        gap: var(--space-3);
      }
      .strength-list__item {
        display: grid;
        grid-template-columns: 16px 1fr;
        gap: var(--space-3);
      }
      .strength-list__icon {
        color: var(--positive);
        margin-top: 2px;
      }
      .strength-list__body {
        display: flex;
        flex-direction: column;
        gap: 2px;
      }
      .strength-list__requirement {
        font-weight: 500;
        color: var(--ink-primary);
      }
      .strength-list__explanation {
        margin: 0;
        max-width: 65ch;
      }
    `,
  ],
})
export class StrengthListComponent {
  @Input({ required: true }) evaluations!: RequirementEvaluation[];

  get strengths(): RequirementEvaluation[] {
    return this.evaluations.filter((evaluation) => evaluation.status === 'MET');
  }
}
