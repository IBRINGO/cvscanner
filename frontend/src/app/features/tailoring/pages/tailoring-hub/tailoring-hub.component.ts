import { DatePipe } from '@angular/common';
import { ChangeDetectionStrategy, Component, OnInit, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { NgIcon, provideIcons } from '@ng-icons/core';
import { CVSCANNER_ICONS } from '../../../../core/icons';
import { TailoringPlanSummary } from '../../models/tailoring.model';
import { TailoringApiService } from '../../services/tailoring-api.service';

/**
 * The generic "Tailoring" nav entry. A tailored CV always starts from
 * an analysis's recommendations - this page lists past tailoring runs
 * and points to that starting point, never a silent redirect to an
 * unrelated page.
 */
@Component({
  selector: 'app-tailoring-hub-page',
  standalone: true,
  imports: [RouterLink, DatePipe, NgIcon],
  viewProviders: [provideIcons(CVSCANNER_ICONS)],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <h1>Tailoring</h1>
    <p class="text-secondary">
      A tailored CV starts from an analysis's recommendations - select the ones you want applied,
      then generate. Nothing outside your verified experience is ever added.
    </p>

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
        @for (plan of plans(); track plan.id) {
          <li class="document-index__row">
            <a [routerLink]="['/tailoring', plan.id]" class="document-index__link">
              <span class="document-index__name">
                {{ plan.mode === 'CONSERVATIVE' ? 'Conservative' : 'Aggressive but safe' }} tailoring -
                {{ plan.created_at | date: 'mediumDate' }}
              </span>
              <span class="document-index__meta text-tertiary font-mono">{{ plan.status }}</span>
            </a>
            <ng-icon name="lucideArrowUpRight" size="16" class="text-tertiary" />
          </li>
        }
      </ul>
    }
  `,
  styles: [
    `
      .tailoring-hub__empty {
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
export class TailoringHubComponent implements OnInit {
  protected readonly plans = signal<TailoringPlanSummary[]>([]);
  protected readonly loading = signal(true);

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
}
