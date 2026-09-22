import { ChangeDetectionStrategy, Component, Input } from '@angular/core';
import { ProcessingStatus } from '../../../models/document.model';

const LABELS: Record<ProcessingStatus, string> = {
  UPLOADED: 'Received',
  VALIDATING: 'Validating',
  PROCESSING: 'Processing',
  PROCESSED: 'Ready',
  FAILED: 'Failed',
};

@Component({
  selector: 'app-status-badge',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <span class="status-badge" [attr.data-status]="status" role="status">
      <span class="status-badge__dot" aria-hidden="true"></span>
      {{ label }}
    </span>
  `,
  styles: [
    `
      .status-badge {
        display: inline-flex;
        align-items: center;
        gap: var(--space-1);
        padding: 2px var(--space-3);
        border-radius: var(--radius-pill);
        font-size: var(--text-xs);
        font-weight: 500;
        background: var(--surface-sunken);
        color: var(--ink-secondary);
      }
      .status-badge__dot {
        width: 6px;
        height: 6px;
        border-radius: 50%;
        background: currentColor;
      }
      .status-badge[data-status='PROCESSING'] {
        color: var(--status-processing);
        background: var(--accent-tint);
      }
      .status-badge[data-status='PROCESSING'] .status-badge__dot {
        animation: status-pulse 1.4s var(--motion-ease) infinite;
      }
      .status-badge[data-status='PROCESSED'] {
        color: var(--status-processed);
        background: var(--status-processed-tint);
      }
      .status-badge[data-status='FAILED'] {
        color: var(--status-failed);
        background: var(--status-failed-tint);
      }

      @keyframes status-pulse {
        0%,
        100% {
          opacity: 1;
        }
        50% {
          opacity: 0.35;
        }
      }
    `,
  ],
})
export class StatusBadgeComponent {
  @Input({ required: true }) status!: ProcessingStatus;

  get label(): string {
    return LABELS[this.status];
  }
}
