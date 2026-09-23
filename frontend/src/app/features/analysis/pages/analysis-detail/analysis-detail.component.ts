import { DatePipe } from '@angular/common';
import { ChangeDetectionStrategy, Component, DestroyRef, OnInit, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { NgIcon, provideIcons } from '@ng-icons/core';
import { CVSCANNER_ICONS } from '../../../../core/icons';
import { ApplicationProgressComponent } from '../../../../shared/components/ui/application-progress/application-progress.component';
import { pollUntilDone } from '../../../../shared/utils/polling';
import { CvApiService } from '../../../cvs/services/cv-api.service';
import { JobApiService } from '../../../jobs/services/job-api.service';
import { AnalysisProcessingComponent } from '../../components/analysis-processing/analysis-processing.component';
import { GapListComponent } from '../../components/gap-list/gap-list.component';
import { RequirementMatrixComponent } from '../../components/requirement-matrix/requirement-matrix.component';
import { ScorePanelComponent } from '../../components/score-panel/score-panel.component';
import { StrengthListComponent } from '../../components/strength-list/strength-list.component';
import { AnalysisDetail, AnalysisStatus } from '../../models/analysis.model';
import { AnalysisApiService } from '../../services/analysis-api.service';

const TERMINAL_STATUSES = new Set<AnalysisStatus>(['COMPLETED', 'FAILED']);

/**
 * The ATS analysis workspace (Phase 4 section 43): candidate/job context,
 * an editorial score panel, the requirement matrix, and the gap section.
 * No recommendation or CV-tailoring content appears here - Phase 4 stops
 * at explaining the analysis (section 77).
 */
@Component({
  selector: 'app-analysis-detail-page',
  standalone: true,
  imports: [
    RouterLink,
    DatePipe,
    NgIcon,
    AnalysisProcessingComponent,
    ScorePanelComponent,
    RequirementMatrixComponent,
    GapListComponent,
    StrengthListComponent,
    ApplicationProgressComponent,
  ],
  viewProviders: [provideIcons(CVSCANNER_ICONS)],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <a routerLink="/analysis" class="analysis-detail__back">
      <ng-icon name="lucideArrowLeft" size="15" />
      Back to analyses
    </a>

    <app-application-progress [current]="'analysis'" [completed]="['cv', 'job']" />

    @if (candidateName() || jobTitle()) {
      <header class="analysis-detail__context">
        <div class="analysis-detail__party">
          <span class="analysis-detail__party-icon"><ng-icon name="lucideUserRound" size="18" /></span>
          <div>
            <span class="text-tertiary">Candidate</span>
            <p>{{ candidateName() ?? 'Unnamed candidate' }}</p>
          </div>
        </div>
        <div class="analysis-detail__divider" aria-hidden="true"></div>
        <div class="analysis-detail__party">
          <span class="analysis-detail__party-icon analysis-detail__party-icon--job"
            ><ng-icon name="lucideBriefcase" size="18"
          /></span>
          <div>
            <span class="text-tertiary">Position</span>
            <p>{{ jobTitle() ?? 'Untitled role' }}@if (jobCompany()) {, {{ jobCompany() }}}</p>
          </div>
        </div>
      </header>
    }

    @switch (status()) {
      @case (null) {
        <app-analysis-processing />
      }
      @default {
        @if (!isDone()) {
          <app-analysis-processing />
        } @else if (status() === 'FAILED') {
          <section class="analysis-detail__error">
            <span class="analysis-detail__error-icon" aria-hidden="true">
              <ng-icon name="lucideTriangleAlert" size="20" />
            </span>
            <div>
              <h1>This analysis could not be completed</h1>
              <p class="text-secondary">{{ errorMessage() ?? 'An unexpected error occurred.' }}</p>
              <p class="text-tertiary">
                The candidate and job profiles this analysis referenced are unaffected and remain available.
              </p>
            </div>
          </section>
        } @else {
          @if (detail(); as analysis) {
            <div class="analysis-detail__workspace">
              <section class="analysis-detail__section" style="animation-delay: 0ms">
                <h2><span class="analysis-detail__section-icon"><ng-icon name="lucideTarget" size="16" /></span>ATS compatibility</h2>
                @if (analysis.score_breakdown) {
                  <app-score-panel [breakdown]="analysis.score_breakdown" [mandatoryGapCount]="mandatoryGapCount()" />
                }
              </section>

              <section class="analysis-detail__section analysis-detail__section--split" style="animation-delay: 60ms">
                <div>
                  <h2>
                    <span class="analysis-detail__section-icon analysis-detail__section-icon--positive"
                      ><ng-icon name="lucideCircleCheck" size="16"
                    /></span>
                    What is working
                  </h2>
                  <app-strength-list [evaluations]="analysis.requirement_evaluations" />
                </div>
                <div>
                  <h2>
                    <span class="analysis-detail__section-icon analysis-detail__section-icon--attention"
                      ><ng-icon name="lucideCircleAlert" size="16"
                    /></span>
                    What needs attention
                  </h2>
                  <app-gap-list [gaps]="analysis.gaps" />
                </div>
              </section>

              <section class="analysis-detail__section" style="animation-delay: 120ms">
                <h2><span class="analysis-detail__section-icon"><ng-icon name="lucideListChecks" size="16" /></span>Requirement matrix</h2>
                <p class="text-tertiary analysis-detail__summary">
                  {{ analysis.requirement_summary.met }} met, {{ analysis.requirement_summary.partially_met }} partial,
                  {{ analysis.requirement_summary.not_met }} missing
                  @if (analysis.requirement_summary.unknown > 0) {, {{ analysis.requirement_summary.unknown }} unknown}
                </p>
                <app-requirement-matrix [evaluations]="analysis.requirement_evaluations" />
              </section>

              <p class="analysis-detail__footer text-tertiary font-mono">
                Engine version {{ analysis.engine_version }} - completed
                {{ analysis.completed_at | date: 'medium' }}
              </p>
            </div>
          }
        }
      }
    }
  `,
  styles: [
    `
      .analysis-detail__back {
        display: inline-flex;
        align-items: center;
        gap: var(--space-1);
        margin-bottom: var(--space-5);
        font-size: var(--text-sm);
        font-weight: 500;
        color: var(--ink-secondary);
        text-decoration: none;
        transition: color var(--motion-fast) var(--motion-ease);
      }
      .analysis-detail__back:hover {
        color: var(--accent);
      }
      app-application-progress {
        display: block;
        margin-bottom: var(--space-6);
      }
      .analysis-detail__context {
        display: flex;
        align-items: center;
        gap: var(--space-6);
        padding: var(--space-5) var(--space-6);
        margin-bottom: var(--space-6);
        background: var(--surface-raised);
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-lg);
        box-shadow: var(--shadow-document);
        flex-wrap: wrap;
      }
      .analysis-detail__party {
        display: flex;
        align-items: center;
        gap: var(--space-3);
        color: var(--ink-tertiary);
      }
      .analysis-detail__party-icon {
        flex-shrink: 0;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 40px;
        height: 40px;
        border-radius: var(--radius-pill);
        background: var(--gradient-brand);
        color: #fff;
      }
      .analysis-detail__party-icon--job {
        background: var(--surface-sunken);
        color: var(--ink-secondary);
      }
      .analysis-detail__party p {
        margin: 2px 0 0;
        color: var(--ink-primary);
        font-weight: 500;
      }
      .analysis-detail__divider {
        width: 1px;
        align-self: stretch;
        background: var(--border-subtle);
      }
      .analysis-detail__workspace {
        display: flex;
        flex-direction: column;
        gap: var(--space-6);
        max-width: 860px;
      }
      .analysis-detail__section {
        padding: var(--space-6);
        background: var(--surface-raised);
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-lg);
        box-shadow: var(--shadow-document);
        animation: analysis-section-in var(--motion-slow) var(--motion-ease) both;
      }
      .analysis-detail__section h2 {
        display: flex;
        align-items: center;
        gap: var(--space-2);
        margin-bottom: var(--space-4);
      }
      .analysis-detail__section-icon {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 28px;
        height: 28px;
        border-radius: var(--radius-sm);
        background: var(--accent-tint);
        color: var(--accent-strong);
        flex-shrink: 0;
      }
      .analysis-detail__section-icon--positive {
        background: var(--positive-tint);
        color: var(--positive);
      }
      .analysis-detail__section-icon--attention {
        background: var(--attention-tint);
        color: var(--attention);
      }
      .analysis-detail__section--split {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: var(--space-7);
      }
      @media (max-width: 760px) {
        .analysis-detail__section--split {
          grid-template-columns: 1fr;
          gap: var(--space-6);
        }
      }
      .analysis-detail__summary {
        margin: 0 0 var(--space-3);
        font-size: var(--text-sm);
      }
      .analysis-detail__error {
        display: flex;
        align-items: flex-start;
        gap: var(--space-3);
        max-width: 560px;
        padding: var(--space-6);
        background: var(--negative-tint);
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-lg);
      }
      .analysis-detail__error-icon {
        flex-shrink: 0;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 36px;
        height: 36px;
        border-radius: var(--radius-pill);
        background: var(--surface-raised);
        color: var(--negative);
      }
      .analysis-detail__footer {
        font-size: var(--text-xs);
      }

      @keyframes analysis-section-in {
        from {
          opacity: 0;
          transform: translateY(14px);
        }
        to {
          opacity: 1;
          transform: translateY(0);
        }
      }

      @media (prefers-reduced-motion: reduce) {
        .analysis-detail__section {
          animation: none;
        }
      }
      @media (max-width: 640px) {
        .analysis-detail__context {
          flex-direction: column;
          align-items: flex-start;
          gap: var(--space-3);
        }
        .analysis-detail__divider {
          display: none;
        }
      }
    `,
  ],
})
export class AnalysisDetailComponent implements OnInit {
  protected readonly status = signal<AnalysisStatus | null>(null);
  protected readonly errorMessage = signal<string | null>(null);
  protected readonly detail = signal<AnalysisDetail | null>(null);
  protected readonly candidateName = signal<string | null>(null);
  protected readonly jobTitle = signal<string | null>(null);
  protected readonly jobCompany = signal<string | null>(null);

  private readonly route = inject(ActivatedRoute);
  private readonly destroyRef = inject(DestroyRef);

  constructor(
    private readonly analysisApi: AnalysisApiService,
    private readonly cvApi: CvApiService,
    private readonly jobApi: JobApiService,
  ) {}

  ngOnInit(): void {
    const analysisId = this.route.snapshot.paramMap.get('id');
    if (!analysisId) return;

    this.analysisApi.getAnalysis(analysisId).subscribe((initial) => {
      this.loadContext(initial.candidate_document_id, initial.job_document_id);
    });

    pollUntilDone(
      () => this.analysisApi.getAnalysisStatus(analysisId),
      (response) => TERMINAL_STATUSES.has(response.status),
    )
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((response) => {
        this.status.set(response.status);
        this.errorMessage.set(response.error);
        if (response.status === 'COMPLETED') {
          this.analysisApi.getAnalysis(analysisId).subscribe((full) => this.detail.set(full));
        }
      });
  }

  isDone(): boolean {
    const current = this.status();
    return current !== null && TERMINAL_STATUSES.has(current);
  }

  mandatoryGapCount(): number {
    return (this.detail()?.gaps ?? []).filter((gap) => gap.priority === 'MANDATORY').length;
  }

  private loadContext(candidateDocumentId: string, jobDocumentId: string): void {
    this.cvApi.getProfile(candidateDocumentId).subscribe((response) => {
      this.candidateName.set(response.profile?.full_name ?? null);
    });
    this.jobApi.getProfile(jobDocumentId).subscribe((response) => {
      this.jobTitle.set(response.profile?.title ?? null);
      this.jobCompany.set(response.profile?.company ?? null);
    });
  }
}
