import { DatePipe, PercentPipe } from '@angular/common';
import { ChangeDetectionStrategy, Component, OnInit, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { NgIcon, provideIcons } from '@ng-icons/core';
import { CVSCANNER_ICONS } from '../../../../core/icons';
import { TailoringMode, TailoringPlanSummary, TailoringStatus } from '../../models/tailoring.model';
import { TailoringApiService } from '../../services/tailoring-api.service';

const MODE_ICONS: Record<TailoringMode, string> = {
  CONSERVATIVE: 'lucideShieldCheck',
  AGGRESSIVE_SAFE: 'lucideZap',
};

const MODE_LABELS: Record<TailoringMode, string> = {
  CONSERVATIVE: 'Conservative',
  AGGRESSIVE_SAFE: 'Aggressive but safe',
};

const STATUS_LABELS: Record<TailoringStatus, string> = {
  PENDING: 'Pending',
  PLANNING: 'Planning',
  GENERATING: 'Generating',
  VALIDATING: 'Validating',
  COMPLETED: 'Completed',
  FAILED: 'Failed',
};

/**
 * The generic "Tailoring" nav entry. A tailored CV always starts from
 * an analysis's recommendations - this page lists past tailoring runs
 * and points to that starting point, never a silent redirect to an
 * unrelated page. Styled to match the cv-list/analysis-list history
 * pattern (icon-badged rows in an elevated panel) instead of the
 * plain text list this page started with.
 */
@Component({
  selector: 'app-tailoring-hub-page',
  standalone: true,
  imports: [RouterLink, DatePipe, PercentPipe, NgIcon],
  viewProviders: [provideIcons(CVSCANNER_ICONS)],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <h1>Tailoring</h1>
    <p class="text-secondary">
      A tailored CV starts from an analysis's recommendations - select the ones you want applied,
      then generate. Nothing outside your verified experience is ever added.
    </p>

    <div class="tailoring-hub__panel">
      @if (loading()) {
        <p class="text-secondary">Loading tailoring runs...</p>
      } @else if (plans().length === 0) {
        <p class="tailoring-hub__empty text-secondary">
          <ng-icon name="lucideInbox" size="16" />
          No tailored CVs yet.
          <a routerLink="/analysis">Start from an analysis.</a>
        </p>
      } @else {
        <ul class="document-index">
          @for (plan of plans(); track plan.id; let i = $index) {
            <li class="document-index__row" [style.animation-delay.ms]="i * 40">
              <a [routerLink]="['/tailoring', plan.id]" class="document-index__link">
                <span class="document-index__icon">
                  <ng-icon [name]="modeIcons[plan.mode]" size="16" />
                </span>
                <span class="document-index__text">
                  <span class="document-index__name">{{ modeLabels[plan.mode] }}</span>
                  <span class="document-index__meta text-tertiary">
                    {{ plan.created_at | date: 'mediumDate' }}
                    @if (plan.status === 'COMPLETED' && plan.before_score != null && plan.after_score != null) {
                      · {{ plan.before_score | percent: '1.0-0' }} to {{ plan.after_score | percent: '1.0-0' }}
                    }
                  </span>
                </span>
              </a>
              <span class="document-index__row-end">
                <span class="tailoring-hub__badge" [attr.data-status]="plan.status">
                  {{ statusLabels[plan.status] }}
                </span>
                <button
                  type="button"
                  class="document-index__delete"
                  title="Delete"
                  [disabled]="deletingIds().has(plan.id)"
                  (click)="deletePlan(plan.id)"
                >
                  <ng-icon name="lucideTrash2" size="15" />
                </button>
                <ng-icon name="lucideArrowUpRight" size="16" class="text-tertiary" />
              </span>
            </li>
          }
        </ul>
        @if (deleteError()) {
          <p class="tailoring-hub__delete-error">{{ deleteError() }}</p>
        }
      }
    </div>
  `,
  styles: [
    `
      .tailoring-hub__panel {
        margin-top: var(--space-5);
        padding: var(--space-5);
        background: var(--surface-raised);
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-lg);
        box-shadow: var(--shadow-document);
        max-width: 640px;
      }
      .tailoring-hub__empty {
        display: inline-flex;
        align-items: center;
        gap: var(--space-2);
      }
      .document-index {
        list-style: none;
        margin: 0;
        padding: 0;
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
        animation: tailoring-row-in var(--motion-slow) var(--motion-ease) both;
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
      .document-index__row-end {
        display: flex;
        align-items: center;
        gap: var(--space-3);
        flex-shrink: 0;
      }
      .tailoring-hub__badge {
        font-family: var(--font-mono);
        font-size: var(--text-xs);
        font-weight: 500;
        color: var(--ink-tertiary);
        white-space: nowrap;
      }
      .tailoring-hub__badge[data-status='COMPLETED'] {
        color: var(--positive);
      }
      .tailoring-hub__badge[data-status='FAILED'] {
        color: var(--negative);
      }
      .tailoring-hub__badge[data-status='PENDING'],
      .tailoring-hub__badge[data-status='PLANNING'],
      .tailoring-hub__badge[data-status='GENERATING'],
      .tailoring-hub__badge[data-status='VALIDATING'] {
        color: var(--accent);
      }
      .document-index__delete {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 28px;
        height: 28px;
        border: none;
        background: none;
        color: var(--ink-tertiary);
        border-radius: var(--radius-sm);
        cursor: pointer;
        transition: background var(--motion-fast) var(--motion-ease), color var(--motion-fast) var(--motion-ease);
      }
      .document-index__delete:hover:not(:disabled) {
        background: var(--negative-tint);
        color: var(--negative);
      }
      .document-index__delete:disabled {
        opacity: 0.4;
        cursor: default;
      }
      .tailoring-hub__delete-error {
        margin: var(--space-3) 0 0;
        padding: var(--space-2) var(--space-3);
        background: var(--negative-tint);
        color: var(--negative);
        border-radius: var(--radius-sm);
        font-size: var(--text-sm);
      }

      @keyframes tailoring-row-in {
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
export class TailoringHubComponent implements OnInit {
  protected readonly plans = signal<TailoringPlanSummary[]>([]);
  protected readonly loading = signal(true);
  protected readonly modeIcons = MODE_ICONS;
  protected readonly modeLabels = MODE_LABELS;
  protected readonly statusLabels = STATUS_LABELS;
  protected readonly deletingIds = signal<ReadonlySet<string>>(new Set());
  protected readonly deleteError = signal<string | null>(null);

  constructor(private readonly tailoringApi: TailoringApiService) {}

  ngOnInit(): void {
    this.tailoringApi.list().subscribe({
      next: (plans) => {
        this.plans.set(plans);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }

  deletePlan(planId: string): void {
    if (this.deletingIds().has(planId)) return;
    const confirmed = window.confirm(
      'Delete this tailored CV run? The analysis and CV/job documents it came from are not affected.',
    );
    if (!confirmed) return;

    this.deleteError.set(null);
    this.deletingIds.update((ids) => new Set(ids).add(planId));
    this.tailoringApi.delete(planId).subscribe({
      next: () => {
        this.plans.update((plans) => plans.filter((plan) => plan.id !== planId));
        this.clearDeleting(planId);
      },
      error: () => {
        this.deleteError.set('Could not delete this tailoring run. Please try again.');
        this.clearDeleting(planId);
      },
    });
  }

  private clearDeleting(planId: string): void {
    this.deletingIds.update((ids) => {
      const next = new Set(ids);
      next.delete(planId);
      return next;
    });
  }
}
