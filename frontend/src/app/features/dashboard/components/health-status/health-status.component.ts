import { ChangeDetectionStrategy, Component, OnInit, signal } from '@angular/core';
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
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="health-status" [attr.data-status]="status()">
      @switch (status()) {
        @case ('loading') {
          <span>Checking backend status…</span>
        }
        @case ('available') {
          <span>✅ Backend available — {{ response()?.service }} v{{ response()?.version }}</span>
        }
        @case ('unavailable') {
          <span>⚠️ Backend unavailable. Is the Django server running?</span>
        }
      }
    </div>
  `,
  styles: [
    `
      .health-status {
        padding: 0.75rem 1rem;
        border-radius: 6px;
        border: 1px solid var(--color-border, #d0d5dd);
        font-size: 0.9rem;
      }
      .health-status[data-status='available'] {
        border-color: #12b76a;
        background: #ecfdf3;
      }
      .health-status[data-status='unavailable'] {
        border-color: #f04438;
        background: #fef3f2;
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
