import { DatePipe } from '@angular/common';
import { ChangeDetectionStrategy, Component, OnInit, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { NgIcon, provideIcons } from '@ng-icons/core';
import { CVSCANNER_ICONS } from '../../../../core/icons';
import { AnalysisSummary } from '../../../analysis/models/analysis.model';
import { AnalysisApiService } from '../../../analysis/services/analysis-api.service';

/**
 * The generic "Recommendations" nav entry. Recommendations are always
 * scoped to one completed analysis - this page is the real entry point
 * (pick an analysis), never a silent redirect to an unrelated page
 * (the nav label must match what the candidate actually sees next).
 */
@Component({
  selector: 'app-recommendations-hub-page',
  standalone: true,
  imports: [RouterLink, DatePipe, NgIcon],
  viewProviders: [provideIcons(CVSCANNER_ICONS)],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <h1>Recommendations</h1>
    <p class="text-secondary">
      Recommendations are generated from a completed analysis. Choose one below to see what
      CVScanner found.
    </p>

    @if (loading()) {
      <p class="text-secondary">Loading analyses...</p>
    } @else if (completedAnalyses().length === 0) {
      <p class="recommendations-hub__empty text-secondary">
        <ng-icon name="lucideInbox" size="16" />
        No completed analyses yet.
        <a routerLink="/analysis">Run one first.</a>
      </p>
    } @else {
      <ul class="document-index">
        @for (analysis of completedAnalyses(); track analysis.id) {
          <li class="document-index__row">
            <a [routerLink]="['/analysis', analysis.id, 'recommendations']" class="document-index__link">
              <span class="document-index__name">Analysis from {{ analysis.created_at | date: 'mediumDate' }}</span>
              <span class="document-index__meta text-tertiary font-mono">Score {{ round(analysis.overall_score) }}</span>
            </a>
            <ng-icon name="lucideArrowUpRight" size="16" class="text-tertiary" />
          </li>
        }
      </ul>
    }
  `,
  styles: [
    `
      .recommendations-hub__empty {
        display: inline-flex;
        align-items: center;
        gap: var(--space-2);
        margin-top: var(--space-4);
      }
      .document-index {
        list-style: none;
        margin: var(--space-5) 0 0;
        padding: 0;
        border-top: 1px solid var(--border-subtle);
        max-width: 560px;
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
        flex: 1;
      }
      .document-index__name {
        color: var(--ink-primary);
        font-weight: 500;
      }
      .document-index__meta {
        font-size: var(--text-xs);
      }
    `,
  ],
})
export class RecommendationsHubComponent implements OnInit {
  protected readonly analyses = signal<AnalysisSummary[]>([]);
  protected readonly loading = signal(true);
  protected readonly round = (value: number | null) => (value === null ? '-' : Math.round(value * 100));

  protected readonly completedAnalyses = () => this.analyses().filter((a) => a.status === 'COMPLETED');

  constructor(private readonly analysisApi: AnalysisApiService) {}

  ngOnInit(): void {
    this.analysisApi.list().subscribe({
      next: (analyses) => {
        this.analyses.set(analyses);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }
}
