import { ChangeDetectionStrategy, Component, OnInit, signal } from '@angular/core';
import { NgIcon, provideIcons } from '@ng-icons/core';
import { CVSCANNER_ICONS } from '../../../../core/icons';
import { HealthService } from '../../services/health.service';
import { BackendStatus, HealthResponse } from '../../models/health.model';

/**
 * Proves the Angular -> HTTP -> Django -> response round trip described in
 * Phase 1 step 22/37: calls GET /api/v1/health/ and renders one of
 * loading / available / unavailable.
 */
@Component({
  selector: 'app-health-status',
  standalone: true,
  imports: [NgIcon],
  viewProviders: [provideIcons(CVSCANNER_ICONS)],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="health-status" [attr.data-status]="status()">
      @switch (status()) {
        @case ('loading') {
          <ng-icon name="lucideLoaderCircle" class="spin" size="16" />
          <span>Checking backend status...</span>
        }
        @case ('available') {
          <ng-icon name="lucideCircleCheck" size="16" />
          <span>Backend available - {{ response()?.service }} v{{ response()?.version }}</span>
        }
        @case ('unavailable') {
          <ng-icon name="lucideTriangleAlert" size="16" />
          <span>Backend unavailable. Is the Django server running?</span>
        }
      }
    </div>
  `,
  styles: [
    `
      .health-status {
        display: inline-flex;
        align-items: center;
        gap: var(--space-2);
        padding: var(--space-2) var(--space-4);
        border-radius: var(--radius-md);
        border: 1px solid var(--border-subtle);
        font-size: var(--text-sm);
        color: var(--ink-secondary);
      }
      .health-status[data-status='available'] {
        border-color: var(--status-processed);
        background: var(--status-processed-tint);
        color: var(--status-processed);
      }
      .health-status[data-status='unavailable'] {
        border-color: var(--status-failed);
        background: var(--status-failed-tint);
        color: var(--status-failed);
      }
      .spin {
        animation: health-status-spin 0.8s linear infinite;
      }
      @keyframes health-status-spin {
        to {
          transform: rotate(360deg);
        }
      }
      @media (prefers-reduced-motion: reduce) {
        .spin {
          animation: none;
        }
      }
    `,
  ],
})
export class HealthStatusComponent implements OnInit {
  protected readonly status = signal<BackendStatus>('loading');
  protected readonly response = signal<HealthResponse | null>(null);

  constructor(private readonly healthService: HealthService) {}

  ngOnInit(): void {
    this.healthService.check().subscribe({
      next: (response) => {
        this.response.set(response);
        this.status.set('available');
      },
      error: () => {
        this.status.set('unavailable');
      },
    });
  }
}
