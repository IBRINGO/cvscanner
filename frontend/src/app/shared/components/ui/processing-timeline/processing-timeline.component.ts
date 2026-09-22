import { ChangeDetectionStrategy, Component, Input } from '@angular/core';
import { ProcessingStatus } from '../../../models/document.model';

interface Stage {
  status: ProcessingStatus;
  label: string;
}

// Exactly the statuses the backend actually reports (section 43: "do not
// fake real-time progress...if detailed progress is not yet available,
// communicate state honestly"). No invented sub-stages.
const STAGES: Stage[] = [
  { status: 'UPLOADED', label: 'Received' },
  { status: 'VALIDATING', label: 'Validating' },
  { status: 'PROCESSING', label: 'Processing' },
  { status: 'PROCESSED', label: 'Ready' },
];

@Component({
  selector: 'app-processing-timeline',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <ol class="timeline" [attr.data-failed]="status === 'FAILED'">
      @for (stage of stages; track stage.status; let i = $index) {
        <li
          class="timeline__stage"
          [attr.data-state]="stateFor(i)"
        >
          <span class="timeline__marker" aria-hidden="true"></span>
          <span class="timeline__label">{{ stage.label }}</span>
        </li>
      }
      @if (status === 'FAILED') {
        <li class="timeline__stage" data-state="failed">
          <span class="timeline__marker" aria-hidden="true"></span>
          <span class="timeline__label">Failed</span>
        </li>
      }
    </ol>
  `,
  styles: [
    `
      .timeline {
        display: flex;
        gap: var(--space-4);
        list-style: none;
        padding: 0;
        margin: 0;
      }
      .timeline__stage {
        display: flex;
        align-items: center;
        gap: var(--space-2);
        color: var(--ink-tertiary);
        font-size: var(--text-sm);
      }
      .timeline__marker {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: var(--border-strong);
      }
      .timeline__stage[data-state='done'] {
        color: var(--ink-secondary);
      }
      .timeline__stage[data-state='done'] .timeline__marker {
        background: var(--status-processed);
      }
      .timeline__stage[data-state='active'] {
        color: var(--ink-primary);
        font-weight: 500;
      }
      .timeline__stage[data-state='active'] .timeline__marker {
        background: var(--status-processing);
        animation: timeline-pulse 1.4s var(--motion-ease) infinite;
      }
      .timeline__stage[data-state='failed'] {
        color: var(--status-failed);
        font-weight: 500;
      }
      .timeline__stage[data-state='failed'] .timeline__marker {
        background: var(--status-failed);
      }

      @keyframes timeline-pulse {
        0%,
        100% {
          transform: scale(1);
        }
        50% {
          transform: scale(1.4);
        }
      }
    `,
  ],
})
export class ProcessingTimelineComponent {
  @Input({ required: true }) status!: ProcessingStatus;

  protected readonly stages = STAGES;

  stateFor(index: number): 'done' | 'active' | 'pending' {
    const currentIndex = STAGES.findIndex((stage) => stage.status === this.status);
    const effectiveIndex = this.status === 'FAILED' ? this.stages.length : currentIndex;
    if (index < effectiveIndex) return 'done';
    if (index === effectiveIndex) return 'active';
    return 'pending';
  }
}
