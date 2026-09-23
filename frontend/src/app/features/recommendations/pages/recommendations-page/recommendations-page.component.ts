import { ChangeDetectionStrategy, Component, OnInit, computed, inject, signal } from '@angular/core';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { NgIcon, provideIcons } from '@ng-icons/core';
import { CVSCANNER_ICONS } from '../../../../core/icons';
import { AnalysisApiService } from '../../../analysis/services/analysis-api.service';
import { CvApiService } from '../../../cvs/services/cv-api.service';
import { JobApiService } from '../../../jobs/services/job-api.service';
import { TailoringMode } from '../../../tailoring/models/tailoring.model';
import { TailoringApiService } from '../../../tailoring/services/tailoring-api.service';
import { RecommendationListComponent } from '../../components/recommendation-list/recommendation-list.component';
import { Recommendation } from '../../models/recommendation.model';
import { RecommendationApiService } from '../../services/recommendation-api.service';

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
  imports: [RouterLink, NgIcon, RecommendationListComponent],
  viewProviders: [provideIcons(CVSCANNER_ICONS)],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <a [routerLink]="['/analysis', analysisId]" class="recommendations-page__back text-secondary">
      Back to analysis
    </a>

    @if (candidateName() || jobTitle()) {
      <header class="recommendations-page__context">
        <div class="recommendations-page__party">
          <ng-icon name="lucideUserRound" size="18" />
          <div>
            <span class="text-tertiary">Candidate</span>
            <p>{{ candidateName() ?? 'Unnamed candidate' }}</p>
          </div>
        </div>
        <div class="recommendations-page__divider" aria-hidden="true"></div>
        <div class="recommendations-page__party">
          <ng-icon name="lucideBriefcase" size="18" />
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
          <h2>Create a tailored CV</h2>
          <p class="text-secondary">
            Choose how much CVScanner may rephrase. Nothing outside your verified experience is ever added.
          </p>
          <div class="recommendations-page__mode">
            <label>
              <input type="radio" name="mode" value="CONSERVATIVE" [checked]="mode() === 'CONSERVATIVE'" (change)="mode.set('CONSERVATIVE')" />
              Conservative - reorder and normalize wording only
            </label>
            <label>
              <input type="radio" name="mode" value="AGGRESSIVE_SAFE" [checked]="mode() === 'AGGRESSIVE_SAFE'" (change)="mode.set('AGGRESSIVE_SAFE')" />
              Aggressive but safe - may rewrite bullets, never invents facts
            </label>
          </div>
          <button
            type="button"
            class="recommendations-page__submit"
            [disabled]="selectedIds().length === 0 || creating()"
            (click)="createTailoringPlan()"
          >
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
        display: inline-block;
        margin-bottom: var(--space-5);
        font-size: var(--text-sm);
        text-decoration: none;
      }
      .recommendations-page__context {
        display: flex;
        align-items: center;
        gap: var(--space-5);
        padding-bottom: var(--space-5);
        margin-bottom: var(--space-6);
        border-bottom: 1px solid var(--border-subtle);
        flex-wrap: wrap;
      }
      .recommendations-page__party {
        display: flex;
        align-items: flex-start;
        gap: var(--space-2);
        color: var(--ink-tertiary);
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
        padding-top: var(--space-5);
        border-top: 1px solid var(--border-subtle);
        max-width: 560px;
      }
      .recommendations-page__mode {
        display: flex;
        flex-direction: column;
        gap: var(--space-2);
        margin: var(--space-4) 0;
        font-size: var(--text-sm);
      }
      .recommendations-page__mode label {
        display: flex;
        align-items: center;
        gap: var(--space-2);
      }
      .recommendations-page__submit {
        font: inherit;
        font-weight: 500;
        padding: var(--space-2) var(--space-5);
        border-radius: var(--radius-sm);
        border: none;
        background: var(--accent);
        color: white;
        cursor: pointer;
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
        this.router.navigate(['/tailoring', plan.id]);
      },
      error: (err) => {
        this.creating.set(false);
        this.createError.set(err?.error?.detail ?? 'Could not start tailoring. Please try again.');
      },
    });
  }
}
