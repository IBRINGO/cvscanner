import { ChangeDetectionStrategy, Component, OnInit, computed, inject, signal } from '@angular/core';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { NgIcon, provideIcons } from '@ng-icons/core';
import { CVSCANNER_ICONS } from '../../../../core/icons';
import { ApplicationProgressComponent } from '../../../../shared/components/ui/application-progress/application-progress.component';
import { AnalysisApiService } from '../../../analysis/services/analysis-api.service';
import { CvApiService } from '../../../cvs/services/cv-api.service';
import { JobApiService } from '../../../jobs/services/job-api.service';
import { TailoringMode } from '../../../tailoring/models/tailoring.model';
import { TailoringApiService } from '../../../tailoring/services/tailoring-api.service';
import { RecommendationListComponent } from '../../components/recommendation-list/recommendation-list.component';
import { Recommendation } from '../../models/recommendation.model';
import { RecommendationApiService } from '../../services/recommendation-api.service';
import { ApplicationSessionService } from '../../../applications/services/application-session.service';

/**
 * The recommendations workspace for one analysis (Phase 5 sections
 * 43-46): what should improve, why, how important, and whether
 * CVScanner can safely act on it. The candidate reviews and selects
 * recommendations here, then chooses a tailoring mode - nothing is
 * rewritten until they explicitly ask for it (section 28).
 */
@Component({
  selector: 'app-recommendations-page',
  standalone: true,
  imports: [RouterLink, NgIcon, RecommendationListComponent, ApplicationProgressComponent],
  viewProviders: [provideIcons(CVSCANNER_ICONS)],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <a [routerLink]="['/analysis', analysisId]" class="recommendations-page__back">
      <ng-icon name="lucideArrowLeft" size="15" />
      Back to analysis
    </a>

    <app-application-progress [current]="'recommendations'" [completed]="['cv', 'job', 'analysis']" />

    @if (candidateName() || jobTitle()) {
      <header class="recommendations-page__context">
        <div class="recommendations-page__party">
          <span class="recommendations-page__party-icon"><ng-icon name="lucideUserRound" size="18" /></span>
          <div>
            <span class="text-tertiary">Candidate</span>
            <p>{{ candidateName() ?? 'Unnamed candidate' }}</p>
          </div>
        </div>
        <div class="recommendations-page__divider" aria-hidden="true"></div>
        <div class="recommendations-page__party">
          <span class="recommendations-page__party-icon recommendations-page__party-icon--job"
            ><ng-icon name="lucideBriefcase" size="18"
          /></span>
          <div>
            <span class="text-tertiary">Position</span>
            <p>{{ jobTitle() ?? 'Untitled role' }}</p>
          </div>
        </div>
      </header>
    }

    <h1>Improve your CV for this position</h1>

    @if (loading()) {
      <p class="text-secondary">Loading recommendations...</p>
    } @else if (recommendations().length === 0) {
      <p class="recommendations-page__empty text-secondary">
        <ng-icon name="lucideCircleCheck" size="16" />
        No recommendations - this analysis found nothing evidence-backed to improve right now.
      </p>
    } @else {
      <p class="text-tertiary recommendations-page__summary">
        {{ recommendations().length }} recommendation{{ recommendations().length === 1 ? '' : 's' }},
        {{ criticalOrHighCount() }} high priority
      </p>

      <app-recommendation-list [recommendations]="recommendations()" (selectionChange)="onSelectionChange($event)" />

      @if (safeToTailorCount() > 0) {
        <section class="recommendations-page__tailor">
          <h2><span class="recommendations-page__tailor-icon"><ng-icon name="lucideSparkles" size="18" /></span>Create a tailored CV</h2>
          <p class="text-secondary">
            Choose how much CVScanner may rephrase. Nothing outside your verified experience is ever added.
          </p>
          <div class="recommendations-page__mode">
            <label class="recommendations-page__mode-option" [attr.data-checked]="mode() === 'CONSERVATIVE'">
              <span class="recommendations-page__mode-head">
                <input type="radio" name="mode" value="CONSERVATIVE" [checked]="mode() === 'CONSERVATIVE'" (change)="mode.set('CONSERVATIVE')" />
                <ng-icon name="lucideShieldCheck" size="16" class="recommendations-page__mode-icon" />
                <span class="recommendations-page__mode-title">Conservative</span>
              </span>
              <span class="text-secondary">Reorder and normalize wording only.</span>
            </label>
            <label class="recommendations-page__mode-option" [attr.data-checked]="mode() === 'AGGRESSIVE_SAFE'">
              <span class="recommendations-page__mode-head">
                <input type="radio" name="mode" value="AGGRESSIVE_SAFE" [checked]="mode() === 'AGGRESSIVE_SAFE'" (change)="mode.set('AGGRESSIVE_SAFE')" />
                <ng-icon name="lucideZap" size="16" class="recommendations-page__mode-icon" />
                <span class="recommendations-page__mode-title">Aggressive but safe</span>
              </span>
              <span class="text-secondary">May rewrite bullets. Never invents facts.</span>
            </label>
          </div>
          <button
            type="button"
            class="recommendations-page__submit"
            [disabled]="selectedIds().length === 0 || creating()"
            (click)="createTailoringPlan()"
          >
            <ng-icon name="lucideSparkles" size="15" />
            {{ creating() ? 'Starting...' : 'Tailor ' + selectedIds().length + ' selected' }}
          </button>
          @if (createError()) {
            <p class="recommendations-page__error">{{ createError() }}</p>
          }
        </section>
      }
    }
  `,
  styles: [
    `
      .recommendations-page__back {
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
      .recommendations-page__back:hover {
        color: var(--accent);
      }
      app-application-progress {
        display: block;
        margin-bottom: var(--space-6);
      }
      .recommendations-page__context {
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
      .recommendations-page__party {
        display: flex;
        align-items: center;
        gap: var(--space-3);
        color: var(--ink-tertiary);
      }
      .recommendations-page__party-icon {
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
      .recommendations-page__party-icon--job {
        background: var(--surface-sunken);
        color: var(--ink-secondary);
      }
      .recommendations-page__party p {
        margin: 2px 0 0;
        color: var(--ink-primary);
        font-weight: 500;
      }
      .recommendations-page__divider {
        width: 1px;
        align-self: stretch;
        background: var(--border-subtle);
      }
      .recommendations-page__summary {
        margin: 0 0 var(--space-5);
        font-size: var(--text-sm);
      }
      .recommendations-page__empty {
        display: inline-flex;
        align-items: center;
        gap: var(--space-2);
      }
      .recommendations-page__tailor {
        margin-top: var(--space-6);
        padding: var(--space-6);
        background: var(--surface-raised);
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-lg);
        box-shadow: var(--shadow-document);
        max-width: 560px;
      }
      .recommendations-page__tailor h2 {
        display: flex;
        align-items: center;
        gap: var(--space-2);
      }
      .recommendations-page__tailor-icon {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 28px;
        height: 28px;
        border-radius: var(--radius-sm);
        background: var(--accent-tint);
        color: var(--accent-strong);
      }
      .recommendations-page__mode {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: var(--space-3);
        margin: var(--space-4) 0;
      }
      .recommendations-page__mode-option {
        display: flex;
        flex-direction: column;
        gap: var(--space-1);
        padding: var(--space-4);
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-md);
        cursor: pointer;
        transition:
          border-color var(--motion-fast) var(--motion-ease),
          background var(--motion-fast) var(--motion-ease);
      }
      .recommendations-page__mode-head {
        display: flex;
        align-items: center;
        gap: var(--space-2);
      }
      .recommendations-page__mode-icon {
        color: var(--ink-tertiary);
      }
      .recommendations-page__mode-option:hover {
        border-color: var(--border-strong);
      }
      .recommendations-page__mode-option[data-checked='true'] {
        border-color: var(--accent);
        background: var(--accent-tint);
      }
      .recommendations-page__mode-option[data-checked='true'] .recommendations-page__mode-icon {
        color: var(--accent-strong);
      }
      .recommendations-page__mode-option input {
        accent-color: var(--accent);
        cursor: pointer;
      }
      .recommendations-page__mode-title {
        font-weight: 600;
        color: var(--ink-primary);
      }
      .recommendations-page__mode-option .text-secondary {
        font-size: var(--text-sm);
      }
      @media (max-width: 560px) {
        .recommendations-page__mode {
          grid-template-columns: 1fr;
        }
      }
      .recommendations-page__submit {
        display: inline-flex;
        align-items: center;
        gap: var(--space-2);
        font: inherit;
        font-weight: 600;
        padding: var(--space-2) var(--space-5);
        border-radius: var(--radius-sm);
        border: none;
        background: var(--accent);
        color: white;
        cursor: pointer;
        transition:
          background var(--motion-fast) var(--motion-ease),
          transform var(--motion-fast) var(--motion-ease);
      }
      .recommendations-page__submit:hover:not(:disabled) {
        background: var(--accent-strong);
        transform: translateY(-1px);
      }
      .recommendations-page__submit:disabled {
        opacity: 0.6;
        cursor: default;
      }
      .recommendations-page__error {
        margin-top: var(--space-3);
        color: var(--match-negative);
        font-size: var(--text-sm);
      }

      @media (prefers-reduced-motion: reduce) {
        .recommendations-page__submit,
        .recommendations-page__mode-option {
          transition: none;
        }
      }

      @media (max-width: 640px) {
        .recommendations-page__context {
          flex-direction: column;
          align-items: flex-start;
          gap: var(--space-3);
        }
        .recommendations-page__divider {
          display: none;
        }
      }
    `,
  ],
})
export class RecommendationsPageComponent implements OnInit {
  protected readonly recommendations = signal<Recommendation[]>([]);
  protected readonly loading = signal(true);
  protected readonly candidateName = signal<string | null>(null);
  protected readonly jobTitle = signal<string | null>(null);
  protected readonly selectedIds = signal<string[]>([]);
  protected readonly mode = signal<TailoringMode>('CONSERVATIVE');
  protected readonly creating = signal(false);
  protected readonly createError = signal<string | null>(null);

  protected readonly analysisId: string;

  protected readonly criticalOrHighCount = computed(
    () => this.recommendations().filter((r) => r.priority === 'CRITICAL' || r.priority === 'HIGH').length,
  );
  protected readonly safeToTailorCount = computed(
    () => this.recommendations().filter((r) => r.safe_to_tailor).length,
  );

  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);

  constructor(
    private readonly recommendationApi: RecommendationApiService,
    private readonly tailoringApi: TailoringApiService,
    private readonly analysisApi: AnalysisApiService,
    private readonly cvApi: CvApiService,
    private readonly jobApi: JobApiService,
    private readonly session: ApplicationSessionService,
  ) {
    this.analysisId = this.route.snapshot.paramMap.get('id') ?? '';
  }

  ngOnInit(): void {
    if (!this.analysisId) return;

    this.recommendationApi.getForAnalysis(this.analysisId).subscribe({
      next: (recommendations) => {
        this.recommendations.set(recommendations);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });

    this.analysisApi.getAnalysis(this.analysisId).subscribe((analysis) => {
      this.cvApi.getProfile(analysis.candidate_document_id).subscribe((response) => {
        this.candidateName.set(response.profile?.full_name ?? null);
      });
      this.jobApi.getProfile(analysis.job_document_id).subscribe((response) => {
        this.jobTitle.set(response.profile?.title ?? null);
      });
    });
  }

  onSelectionChange(ids: string[]): void {
    this.selectedIds.set(ids);
  }

  createTailoringPlan(): void {
    if (this.selectedIds().length === 0 || this.creating()) return;

    this.creating.set(true);
    this.createError.set(null);
    this.tailoringApi.create(this.analysisId, this.mode(), this.selectedIds()).subscribe({
      next: (plan) => {
        this.creating.set(false);
        this.session.setAnalysis(this.analysisId);
        this.session.setTailoring(plan.id);
        this.router.navigate(['/tailoring', plan.id]);
      },
      error: (err) => {
        this.creating.set(false);
        this.createError.set(err?.error?.detail ?? 'Could not start tailoring. Please try again.');
      },
    });
  }
}
