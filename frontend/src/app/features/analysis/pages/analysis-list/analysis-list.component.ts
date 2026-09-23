import { DatePipe } from '@angular/common';
import { ChangeDetectionStrategy, Component, OnInit, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { NgIcon, provideIcons } from '@ng-icons/core';
import { CVSCANNER_ICONS } from '../../../../core/icons';
import { DocumentSummary } from '../../../../shared/models/document.model';
import { CvApiService } from '../../../cvs/services/cv-api.service';
import { JobApiService } from '../../../jobs/services/job-api.service';
import { AnalysisSummary } from '../../models/analysis.model';
import { AnalysisApiService } from '../../services/analysis-api.service';

/**
 * The analysis workspace entry point: pick a processed CV and a
 * processed job offer to compare, plus the history of past analyses -
 * mirrors the cv-list/job-list split-panel layout (section 56/67).
 */
@Component({
  selector: 'app-analysis-list-page',
  standalone: true,
  imports: [RouterLink, DatePipe, NgIcon, FormsModule],
  viewProviders: [provideIcons(CVSCANNER_ICONS)],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <section class="analysis-workspace">
      <div class="analysis-workspace__create">
        <h1>Run an ATS analysis</h1>
        <p class="text-secondary">
          Compare a processed CV against a processed job offer: a hybrid, evidence-aware match
          across skills, experience, education, and more - never a bare score.
        </p>

        @if (cvs().length === 0 || jobs().length === 0) {
          <p class="analysis-workspace__empty text-secondary">
            <ng-icon name="lucideInbox" size="16" />
            You need at least one processed
            @if (cvs().length === 0) {<a routerLink="/cvs">CV</a>}
            @if (cvs().length === 0 && jobs().length === 0) { and }
            @if (jobs().length === 0) {<a routerLink="/jobs">job offer</a>}
            before you can run an analysis.
          </p>
        } @else {
          <form class="analysis-workspace__form" (submit)="onSubmit($event)">
            <label class="analysis-workspace__field">
              <span>Candidate CV</span>
              <select [(ngModel)]="selectedCvId" name="cv" required>
                <option [ngValue]="null" disabled>Choose a CV</option>
                @for (cv of cvs(); track cv.id) {
                  <option [ngValue]="cv.id">{{ cv.original_filename }}</option>
                }
              </select>
            </label>
            <label class="analysis-workspace__field">
              <span>Job offer</span>
              <select [(ngModel)]="selectedJobId" name="job" required>
                <option [ngValue]="null" disabled>Choose a job offer</option>
                @for (job of jobs(); track job.id) {
                  <option [ngValue]="job.id">{{ job.original_filename }}</option>
                }
              </select>
            </label>
            <button type="submit" class="analysis-workspace__submit" [disabled]="creating()">
              {{ creating() ? 'Starting...' : 'Run analysis' }}
            </button>
          </form>
        }
      </div>

      <div class="analysis-workspace__list">
        <h2>Recent analyses</h2>
        @if (analyses().length === 0) {
          <p class="text-secondary">No analyses yet. Run your first one to see it here.</p>
        } @else {
          <ul class="document-index">
            @for (analysis of analyses(); track analysis.id) {
              <li class="document-index__row">
                <a [routerLink]="['/analysis', analysis.id]" class="document-index__link">
                  <span class="document-index__name">
                    {{ documentName(analysis.candidate_document_id) }} vs
                    {{ documentName(analysis.job_document_id) }}
                  </span>
                  <span class="document-index__meta text-tertiary font-mono">{{
                    analysis.created_at | date: 'mediumDate'
                  }}</span>
                </a>
                <span class="analysis-workspace__badge" [attr.data-status]="analysis.status">
                  @if (analysis.status === 'COMPLETED' && analysis.overall_score !== null) {
                    {{ round(analysis.overall_score * 100) }}
                  } @else {
                    {{ analysis.status }}
                  }
                </span>
              </li>
            }
          </ul>
        }
      </div>
    </section>
  `,
  styles: [
    `
      .analysis-workspace {
        display: grid;
        grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
        gap: var(--space-7);
        align-items: start;
      }
      .analysis-workspace__create {
        display: flex;
        flex-direction: column;
        gap: var(--space-4);
      }
      .analysis-workspace__empty {
        display: inline-flex;
        align-items: center;
        gap: var(--space-2);
      }
      .analysis-workspace__form {
        display: flex;
        flex-direction: column;
        gap: var(--space-4);
        max-width: 420px;
      }
      .analysis-workspace__field {
        display: flex;
        flex-direction: column;
        gap: var(--space-1);
        font-size: var(--text-sm);
        color: var(--ink-secondary);
      }
      .analysis-workspace__field select {
        font: inherit;
        padding: var(--space-2) var(--space-3);
        border-radius: var(--radius-sm);
        border: 1px solid var(--border-strong);
        background: var(--surface-raised);
        color: var(--ink-primary);
      }
      .analysis-workspace__submit {
        align-self: flex-start;
        font: inherit;
        font-weight: 500;
        padding: var(--space-2) var(--space-5);
        border-radius: var(--radius-sm);
        border: none;
        background: var(--accent);
        color: white;
        cursor: pointer;
        transition: background var(--motion-fast) var(--motion-ease);
      }
      .analysis-workspace__submit:hover:not(:disabled) {
        background: var(--accent-strong);
      }
      .analysis-workspace__submit:disabled {
        opacity: 0.6;
        cursor: default;
      }
      .analysis-workspace__list h2 {
        margin-bottom: var(--space-4);
      }
      .document-index {
        list-style: none;
        margin: 0;
        padding: 0;
        border-top: 1px solid var(--border-subtle);
      }
      .document-index__row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: var(--space-3);
        padding: var(--space-3) 0;
        border-bottom: 1px solid var(--border-subtle);
      }
      .document-index__link {
        display: flex;
        flex-direction: column;
        gap: 2px;
        text-decoration: none;
        min-width: 0;
      }
      .document-index__name {
        color: var(--ink-primary);
        font-weight: 500;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }
      .document-index__meta {
        font-size: var(--text-xs);
      }
      .analysis-workspace__badge {
        font-family: var(--font-mono);
        font-size: var(--text-sm);
        color: var(--ink-tertiary);
        white-space: nowrap;
      }
      .analysis-workspace__badge[data-status='COMPLETED'] {
        color: var(--match-positive);
        font-weight: 500;
      }
      .analysis-workspace__badge[data-status='FAILED'] {
        color: var(--match-negative);
      }

      @media (max-width: 900px) {
        .analysis-workspace {
          grid-template-columns: minmax(0, 1fr);
        }
      }
    `,
  ],
})
export class AnalysisListComponent implements OnInit {
  protected readonly cvs = signal<DocumentSummary[]>([]);
  protected readonly jobs = signal<DocumentSummary[]>([]);
  protected readonly analyses = signal<AnalysisSummary[]>([]);
  protected readonly creating = signal(false);
  protected readonly round = Math.round;

  protected selectedCvId: string | null = null;
  protected selectedJobId: string | null = null;

  constructor(
    private readonly analysisApi: AnalysisApiService,
    private readonly cvApi: CvApiService,
    private readonly jobApi: JobApiService,
    private readonly router: Router,
  ) {}

  ngOnInit(): void {
    this.cvApi.list().subscribe((documents) => this.cvs.set(documents.filter((d) => d.status === 'PROCESSED')));
    this.jobApi.list().subscribe((documents) => this.jobs.set(documents.filter((d) => d.status === 'PROCESSED')));
    this.analysisApi.list().subscribe((analyses) => this.analyses.set(analyses));
  }

  documentName(documentId: string): string {
    const match = [...this.cvs(), ...this.jobs()].find((document) => document.id === documentId);
    return match?.original_filename ?? 'Document';
  }

  onSubmit(event: Event): void {
    event.preventDefault();
    if (!this.selectedCvId || !this.selectedJobId || this.creating()) return;

    this.creating.set(true);
    this.analysisApi.createAnalysis(this.selectedCvId, this.selectedJobId).subscribe({
      next: (analysis) => {
        this.creating.set(false);
        this.router.navigate(['/analysis', analysis.id]);
      },
      error: () => {
        this.creating.set(false);
      },
    });
  }
}
