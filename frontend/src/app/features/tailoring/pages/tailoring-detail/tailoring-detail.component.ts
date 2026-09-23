import { DatePipe } from '@angular/common';
import { ChangeDetectionStrategy, Component, DestroyRef, OnInit, computed, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { NgIcon, provideIcons } from '@ng-icons/core';
import { CVSCANNER_ICONS } from '../../../../core/icons';
import { pollUntilDone } from '../../../../shared/utils/polling';
import { TailoringDiffComponent } from '../../components/tailoring-diff/tailoring-diff.component';
import { TailoringPlanDetail, TailoringStatus } from '../../models/tailoring.model';
import { TailoringApiService } from '../../services/tailoring-api.service';

const TERMINAL_STATUSES = new Set<TailoringStatus>(['COMPLETED', 'FAILED']);
const STAGE_ORDER: TailoringStatus[] = ['PENDING', 'PLANNING', 'GENERATING', 'VALIDATING'];
const STAGE_LABELS: Record<TailoringStatus, string> = {
  PENDING: 'Reviewing recommendations',
  PLANNING: 'Preparing tailoring plan',
  GENERATING: 'Rewriting selected sections',
  VALIDATING: 'Checking factual consistency',
  COMPLETED: 'Finalizing tailored CV',
  FAILED: 'Finalizing tailored CV',
};

/**
 * The tailoring workspace (Phase 5 sections 47-58): a real, honest
 * progress timeline (PENDING/PLANNING/GENERATING/VALIDATING map to
 * actual backend states, never a fabricated percentage), then the
 * before/after score with an explicit disclaimer (section 54), a
 * factual-consistency validation summary (section 56), and every
 * proposed change with its diff - accepted or rejected, never hidden.
 */
@Component({
  selector: 'app-tailoring-detail-page',
  standalone: true,
  imports: [RouterLink, DatePipe, NgIcon, TailoringDiffComponent],
  viewProviders: [provideIcons(CVSCANNER_ICONS)],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    @if (plan(); as summary) {
      <a [routerLink]="['/analysis', summary.analysis_id, 'recommendations']" class="tailoring-detail__back text-secondary">
        Back to recommendations
      </a>
    }

    <h1>Tailored CV</h1>

    @if (!isDone()) {
      <div class="tailoring-detail__progress" role="status" aria-live="polite">
        <ng-icon name="lucideLoaderCircle" class="tailoring-detail__spinner" size="20" />
        <ol class="tailoring-detail__stages">
          @for (stage of stageOrder; track stage) {
            <li [attr.data-state]="stageState(stage)">{{ stageLabels[stage] }}</li>
          }
        </ol>
      </div>
    } @else if (status() === 'FAILED') {
      <section class="tailoring-detail__error">
        <h2>This tailoring run could not be completed</h2>
        <p class="text-secondary">{{ errorMessage() ?? 'An unexpected error occurred.' }}</p>
        <p class="text-tertiary">Your original CV and analysis are unaffected.</p>
      </section>
    } @else {
      @if (plan(); as detail) {
        <div class="tailoring-detail__workspace">
          <section class="tailoring-detail__section">
            <h2><ng-icon name="lucideTarget" size="18" />Alignment before and after</h2>
            <div class="tailoring-detail__scores">
              <div class="tailoring-detail__score">
                <span class="text-tertiary">Before</span>
                <span class="tailoring-detail__score-value">{{ round(detail.before_score) }}</span>
              </div>
              <ng-icon name="lucideArrowUpRight" size="18" class="tailoring-detail__score-arrow" />
              <div class="tailoring-detail__score">
                <span class="text-tertiary">After</span>
                <span class="tailoring-detail__score-value">{{ round(detail.after_score) }}</span>
              </div>
            </div>
            <p class="text-tertiary tailoring-detail__requirements">
              {{ detail.requirements_improved }} requirement{{ detail.requirements_improved === 1 ? '' : 's' }} improved,
              {{ detail.requirements_unchanged }} unchanged,
              {{ detail.requirements_still_missing }} still missing
            </p>
            <p class="tailoring-detail__disclaimer text-tertiary">
              This score reflects alignment with the analyzed job's requirements according to CVScanner's
              deterministic matching engine. It does not guarantee recruiter interest, an interview, or
              employment.
            </p>
          </section>

          <section class="tailoring-detail__section">
            <h2><ng-icon name="lucideClipboardCheck" size="18" />Factual consistency</h2>
            <ul class="tailoring-detail__validation">
              <li><ng-icon name="lucideCircleCheck" size="14" />{{ acceptedCount() }} change{{ acceptedCount() === 1 ? '' : 's' }} verified against your CV</li>
              @if (rejectedCount() > 0) {
                <li>
                  <ng-icon name="lucideTriangleAlert" size="14" />
                  {{ rejectedCount() }} proposed change{{ rejectedCount() === 1 ? '' : 's' }} could not be verified and
                  {{ rejectedCount() === 1 ? 'was' : 'were' }} rejected automatically
                </li>
              }
              <li><ng-icon name="lucideCircleCheck" size="14" />No unsupported technologies, certifications, or dates were introduced</li>
            </ul>
          </section>

          <section class="tailoring-detail__section">
            <h2><ng-icon name="lucideListChecks" size="18" />Changes</h2>
            @for (change of detail.changes; track change.fact_id) {
              <app-tailoring-diff [change]="change" />
            }
          </section>

          <p class="tailoring-detail__footer text-tertiary font-mono">
            {{ detail.mode === 'CONSERVATIVE' ? 'Conservative' : 'Aggressive but safe' }} mode - completed
            {{ detail.completed_at | date: 'medium' }}
          </p>
        </div>
      }
    }
  `,
  styles: [
    `
      .tailoring-detail__back {
        display: inline-block;
        margin-bottom: var(--space-5);
        font-size: var(--text-sm);
        text-decoration: none;
      }
      .tailoring-detail__progress {
        display: flex;
        align-items: center;
        gap: var(--space-5);
        padding: var(--space-6) 0;
        color: var(--ink-tertiary);
      }
      .tailoring-detail__spinner {
        animation: tailoring-detail-spin 0.9s linear infinite;
        flex-shrink: 0;
      }
      .tailoring-detail__stages {
        list-style: none;
        margin: 0;
        padding: 0;
        display: flex;
        flex-direction: column;
        gap: var(--space-1);
      }
      .tailoring-detail__stages li {
        font-size: var(--text-sm);
        opacity: 0.45;
      }
      .tailoring-detail__stages li[data-state='active'] {
        color: var(--ink-primary);
        font-weight: 500;
        opacity: 1;
      }
      .tailoring-detail__stages li[data-state='done'] {
        opacity: 0.8;
      }
      @keyframes tailoring-detail-spin {
        to {
          transform: rotate(360deg);
        }
      }
      .tailoring-detail__error {
        display: flex;
        flex-direction: column;
        gap: var(--space-3);
        max-width: 560px;
      }
      .tailoring-detail__workspace {
        display: flex;
        flex-direction: column;
        gap: var(--space-7);
        max-width: 860px;
      }
      .tailoring-detail__section h2 {
        display: flex;
        align-items: center;
        gap: var(--space-2);
        margin-bottom: var(--space-3);
      }
      .tailoring-detail__scores {
        display: flex;
        align-items: center;
        gap: var(--space-5);
      }
      .tailoring-detail__score {
        display: flex;
        flex-direction: column;
        gap: 2px;
      }
      .tailoring-detail__score-value {
        font-family: var(--font-display);
        font-size: var(--text-2xl);
        color: var(--ink-primary);
      }
      .tailoring-detail__score-arrow {
        color: var(--match-positive);
      }
      .tailoring-detail__requirements {
        margin: var(--space-3) 0 0;
        font-size: var(--text-sm);
      }
      .tailoring-detail__disclaimer {
        margin: var(--space-2) 0 0;
        font-size: var(--text-xs);
        max-width: 60ch;
      }
      .tailoring-detail__validation {
        list-style: none;
        margin: 0;
        padding: 0;
        display: flex;
        flex-direction: column;
        gap: var(--space-2);
        font-size: var(--text-sm);
      }
      .tailoring-detail__validation li {
        display: flex;
        align-items: flex-start;
        gap: var(--space-2);
        color: var(--ink-secondary);
      }
      .tailoring-detail__footer {
        font-size: var(--text-xs);
      }
      @media (prefers-reduced-motion: reduce) {
        .tailoring-detail__spinner {
          animation: none;
        }
      }
    `,
  ],
})
export class TailoringDetailComponent implements OnInit {
  protected readonly status = signal<TailoringStatus | null>(null);
  protected readonly errorMessage = signal<string | null>(null);
  protected readonly plan = signal<TailoringPlanDetail | null>(null);
  protected readonly stageOrder = STAGE_ORDER;
  protected readonly stageLabels = STAGE_LABELS;
  protected readonly round = (value: number | null) => (value === null ? '-' : Math.round(value * 100));

  protected readonly acceptedCount = computed(
    () => (this.plan()?.changes ?? []).filter((c) => c.accepted).length,
  );
  protected readonly rejectedCount = computed(
    () => (this.plan()?.changes ?? []).filter((c) => !c.accepted).length,
  );

  private readonly route = inject(ActivatedRoute);
  private readonly destroyRef = inject(DestroyRef);

  constructor(private readonly tailoringApi: TailoringApiService) {}

  ngOnInit(): void {
    const planId = this.route.snapshot.paramMap.get('id');
    if (!planId) return;

    this.tailoringApi.getPlan(planId).subscribe((summary) => this.plan.set(summary));

    pollUntilDone(
      () => this.tailoringApi.getStatus(planId),
      (response) => TERMINAL_STATUSES.has(response.status),
    )
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((response) => {
        this.status.set(response.status);
        this.errorMessage.set(response.error);
        if (response.status === 'COMPLETED') {
          this.tailoringApi.getPlan(planId).subscribe((full) => this.plan.set(full));
        }
      });
  }

  isDone(): boolean {
    const current = this.status();
    return current !== null && TERMINAL_STATUSES.has(current);
  }

  stageState(stage: TailoringStatus): 'done' | 'active' | 'pending' {
    const current = this.status();
    if (current === null) return stage === 'PENDING' ? 'active' : 'pending';
    const currentIndex = STAGE_ORDER.indexOf(current);
    const stageIndex = STAGE_ORDER.indexOf(stage);
    if (currentIndex === -1) return 'pending';
    if (stageIndex < currentIndex) return 'done';
    if (stageIndex === currentIndex) return 'active';
    return 'pending';
  }
}
