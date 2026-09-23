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
    <header class="recommendations-hub__header">
      <h1>Recommendations</h1>
      <p class="text-secondary">
        Recommendations are generated from a completed analysis. Choose one below to see what
        CVScanner found.
      </p>
    </header>

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
        @for (analysis of completedAnalyses(); track analysis.id; let i = $index) {
          <li class="document-index__row" [style.animation-delay.ms]="i * 40">
            <a [routerLink]="['/analysis', analysis.id, 'recommendations']" class="document-index__link">
              <span class="document-index__icon">
                <ng-icon name="lucideListChecks" size="16" />
              </span>
              <span class="document-index__text">
                <span class="document-index__name">Analysis from {{ analysis.created_at | date: 'mediumDate' }}</span>
                <span class="document-index__meta text-tertiary font-mono">Score {{ round(analysis.overall_score) }}</span>
              </span>
            </a>
            <ng-icon name="lucideArrowUpRight" size="16" class="text-tertiary" />
          </li>
        }
      </ul>
    }
  `,
  styles: [
    `
      .recommendations-hub__header {
        display: flex;
        flex-direction: column;
        gap: var(--space-2);
        margin-bottom: var(--space-6);
        max-width: 640px;
      }
      .recommendations-hub__empty {
        display: inline-flex;
        align-items: center;
        gap: var(--space-2);
      }
      .document-index {
        list-style: none;
        margin: 0;
        padding: var(--space-5);
        border-top: none;
        max-width: 640px;
        background: var(--surface-raised);
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-lg);
        box-shadow: var(--shadow-document);
      }
      .document-index__row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: var(--space-3);
        padding: var(--space-3) var(--space-2);
        margin: 0 calc(var(--space-2) * -1);
        border-bottom: 1px solid var(--border-subtle);
        border-radius: var(--radius-sm);
        animation: document-row-in var(--motion-slow) var(--motion-ease) both;
        transition: background var(--motion-fast) var(--motion-ease);
      }
      .document-index__row:last-child {
        border-bottom: none;
      }
      .document-index__row:hover {
        background: var(--surface-sunken);
      }
      .document-index__link {
        display: flex;
        align-items: center;
        gap: var(--space-3);
        text-decoration: none;
        min-width: 0;
        flex: 1;
      }
      .document-index__icon {
        flex-shrink: 0;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 32px;
        height: 32px;
        border-radius: var(--radius-sm);
        background: var(--accent-tint);
        color: var(--accent-strong);
        transition: transform var(--motion-base) var(--motion-spring);
      }
      .document-index__row:hover .document-index__icon {
        transform: scale(1.08);
      }
      .document-index__text {
        display: flex;
        flex-direction: column;
        gap: 2px;
        min-width: 0;
      }
      .document-index__name {
        color: var(--ink-primary);
        font-weight: 500;
      }
      .document-index__meta {
        font-size: var(--text-xs);
      }

      @keyframes document-row-in {
        from {
          opacity: 0;
          transform: translateX(8px);
        }
        to {
          opacity: 1;
          transform: translateX(0);
        }
      }

      @media (prefers-reduced-motion: reduce) {
        .document-index__row {
          animation: none;
        }
        .document-index__icon {
          transition: none;
        }
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
