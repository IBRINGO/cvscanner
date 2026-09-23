import { ChangeDetectionStrategy, Component, Input } from '@angular/core';
import { NgIcon, provideIcons } from '@ng-icons/core';
import { CVSCANNER_ICONS } from '../../../../core/icons';

export type ApplicationStage = 'cv' | 'job' | 'analysis' | 'recommendations' | 'tailoring' | 'export';

const STAGE_LABELS: Record<ApplicationStage, string> = {
  cv: 'CV',
  job: 'Job',
  analysis: 'Analysis',
  recommendations: 'Recommendations',
  tailoring: 'Tailoring',
  export: 'Export',
};

const STAGE_ORDER: ApplicationStage[] = ['cv', 'job', 'analysis', 'recommendations', 'tailoring', 'export'];

/**
 * The persistent, compact step indicator for a single application's
 * journey (CV -> Job -> Analysis -> Recommendations -> Tailoring ->
 * Export). Reflects real state only: a stage is "done" only when the
 * caller has actual evidence of completion (e.g. an analysis with
 * status COMPLETED), never inferred from navigation history alone.
 */
@Component({
  selector: 'app-application-progress',
  standalone: true,
  imports: [NgIcon],
  viewProviders: [provideIcons(CVSCANNER_ICONS)],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <ol class="progress" [attr.aria-label]="'Application progress'">
      @for (stage of stages; track stage; let last = $last) {
        <li class="progress__step" [attr.data-state]="stateFor(stage)">
          <span class="progress__marker" aria-hidden="true">
            @if (stateFor(stage) === 'done') {
              <ng-icon name="lucideCheck" size="11" />
            }
          </span>
          <span class="progress__label">{{ STAGE_LABELS[stage] }}</span>
          @if (!last) {
            <span class="progress__connector" aria-hidden="true"></span>
          }
        </li>
      }
    </ol>
  `,
  styles: [
    `
      .progress {
        display: flex;
        align-items: center;
        list-style: none;
        margin: 0;
        padding: 0;
        overflow-x: auto;
      }
      .progress__step {
        display: flex;
        align-items: center;
        flex-shrink: 0;
      }
      .progress__marker {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 18px;
        height: 18px;
        border-radius: 50%;
        border: 1.5px solid var(--border-strong);
        color: var(--surface-raised);
        flex-shrink: 0;
      }
      .progress__label {
        margin: 0 var(--space-2);
        font-size: var(--text-xs);
        font-weight: 500;
        color: var(--ink-tertiary);
        white-space: nowrap;
      }
      .progress__connector {
        width: 20px;
        height: 1.5px;
        background: var(--border-subtle);
        margin-right: var(--space-2);
      }
      .progress__step[data-state='done'] .progress__marker {
        background: var(--positive);
        border-color: var(--positive);
      }
      .progress__step[data-state='done'] .progress__label {
        color: var(--ink-secondary);
      }
      .progress__step[data-state='done'] .progress__connector {
        background: var(--positive);
      }
      .progress__step[data-state='active'] .progress__marker {
        border-color: var(--accent);
        background: var(--accent);
        animation: progress-pulse 1.6s var(--motion-ease) infinite;
      }
      .progress__step[data-state='active'] .progress__label {
        color: var(--ink-primary);
        font-weight: 600;
      }

      @keyframes progress-pulse {
        0%,
        100% {
          box-shadow: 0 0 0 0 var(--accent-tint);
        }
        50% {
          box-shadow: 0 0 0 4px var(--accent-tint);
        }
      }

      @media (prefers-reduced-motion: reduce) {
        .progress__step[data-state='active'] .progress__marker {
          animation: none;
        }
      }
    `,
  ],
})
export class ApplicationProgressComponent {
  @Input({ required: true }) current!: ApplicationStage;
  @Input() completed: ApplicationStage[] = [];

  protected readonly stages = STAGE_ORDER;
  protected readonly STAGE_LABELS = STAGE_LABELS;

  stateFor(stage: ApplicationStage): 'done' | 'active' | 'pending' {
    if (stage === this.current) return 'active';
    if (this.completed.includes(stage)) return 'done';
    return 'pending';
  }
}
