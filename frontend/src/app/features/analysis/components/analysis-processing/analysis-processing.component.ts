import { ChangeDetectionStrategy, Component, OnDestroy, OnInit, signal } from '@angular/core';
import { NgIcon, provideIcons } from '@ng-icons/core';
import { CVSCANNER_ICONS } from '../../../../core/icons';

const STAGES = [
  'Reading requirements',
  'Checking skills',
  'Comparing experience',
  'Validating evidence',
  'Building analysis',
];

const STAGE_INTERVAL_MS = 1400;

/**
 * The analysis-processing experience (Phase 4 section 51). These stage
 * labels are illustrative, not literal backend sub-states - the API only
 * ever reports PENDING/PROCESSING/COMPLETED/FAILED. Cycling through them
 * communicates "real work of several kinds is happening" without ever
 * claiming a fake percentage (explicitly forbidden by the brief).
 */
@Component({
  selector: 'app-analysis-processing',
  standalone: true,
  imports: [NgIcon],
  viewProviders: [provideIcons(CVSCANNER_ICONS)],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="analysis-processing" role="status" aria-live="polite">
      <span class="analysis-processing__spinner-ring">
        <ng-icon name="lucideLoaderCircle" class="analysis-processing__spinner" size="22" />
      </span>
      <div class="analysis-processing__body">
        <ul class="analysis-processing__stages">
          @for (stage of stages; track stage; let i = $index) {
            <li [attr.data-active]="i === activeIndex()" [attr.data-done]="i < activeIndex()">
              <span class="analysis-processing__dot" aria-hidden="true"></span>
              {{ stage }}
            </li>
          }
        </ul>
      </div>
    </div>
  `,
  styles: [
    `
      .analysis-processing {
        display: flex;
        align-items: center;
        gap: var(--space-5);
        padding: var(--space-6);
        color: var(--ink-tertiary);
        background: var(--surface-raised);
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-lg);
        box-shadow: var(--shadow-document);
      }
      .analysis-processing__spinner-ring {
        flex-shrink: 0;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 48px;
        height: 48px;
        border-radius: var(--radius-pill);
        background: var(--accent-tint);
        color: var(--accent-strong);
      }
      .analysis-processing__spinner {
        animation: analysis-processing-spin 0.9s linear infinite;
      }
      .analysis-processing__stages {
        list-style: none;
        margin: 0;
        padding: 0;
        display: flex;
        flex-direction: column;
        gap: var(--space-2);
      }
      .analysis-processing__stages li {
        display: flex;
        align-items: center;
        gap: var(--space-2);
        font-size: var(--text-sm);
        transition: color var(--motion-base) var(--motion-ease), opacity var(--motion-base) var(--motion-ease);
        opacity: 0.45;
      }
      .analysis-processing__dot {
        width: 6px;
        height: 6px;
        border-radius: 50%;
        background: var(--border-strong);
        flex-shrink: 0;
        transition: background var(--motion-base) var(--motion-ease);
      }
      .analysis-processing__stages li[data-done='true'] .analysis-processing__dot {
        background: var(--positive);
      }
      .analysis-processing__stages li[data-active='true'] .analysis-processing__dot {
        background: var(--accent);
      }
      .analysis-processing__stages li[data-active='true'] {
        color: var(--ink-primary);
        font-weight: 500;
        opacity: 1;
      }
      @keyframes analysis-processing-spin {
        to {
          transform: rotate(360deg);
        }
      }
      @media (prefers-reduced-motion: reduce) {
        .analysis-processing__spinner {
          animation: none;
        }
        .analysis-processing__stages li {
          transition: none;
        }
      }
    `,
  ],
})
export class AnalysisProcessingComponent implements OnInit, OnDestroy {
  protected readonly stages = STAGES;
  protected readonly activeIndex = signal(0);
  private intervalId?: ReturnType<typeof setInterval>;

  ngOnInit(): void {
    this.intervalId = setInterval(() => {
      this.activeIndex.update((index) => (index + 1) % STAGES.length);
    }, STAGE_INTERVAL_MS);
  }

  ngOnDestroy(): void {
    if (this.intervalId) {
      clearInterval(this.intervalId);
    }
  }
}
