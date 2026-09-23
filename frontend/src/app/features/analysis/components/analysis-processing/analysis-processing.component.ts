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
      <ng-icon name="lucideLoaderCircle" class="analysis-processing__spinner" size="20" />
      <ul class="analysis-processing__stages">
        @for (stage of stages; track stage; let i = $index) {
          <li [attr.data-active]="i === activeIndex()">{{ stage }}</li>
        }
      </ul>
    </div>
  `,
  styles: [
    `
      .analysis-processing {
        display: flex;
        align-items: center;
        gap: var(--space-5);
        padding: var(--space-6) 0;
        color: var(--ink-tertiary);
      }
      .analysis-processing__spinner {
        animation: analysis-processing-spin 0.9s linear infinite;
        flex-shrink: 0;
      }
      .analysis-processing__stages {
        list-style: none;
        margin: 0;
        padding: 0;
        display: flex;
        flex-direction: column;
        gap: var(--space-1);
      }
      .analysis-processing__stages li {
        font-size: var(--text-sm);
        transition: color var(--motion-base) var(--motion-ease), opacity var(--motion-base) var(--motion-ease);
        opacity: 0.45;
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
