import { ChangeDetectionStrategy, Component } from '@angular/core';
import { NotificationService } from '../../../../core/services/notification.service';

/**
 * Renders NotificationService's state (section 44/74: errors must be
 * visible, never silently swallowed). Mounted once in MainLayoutComponent
 * so any feature can call NotificationService.error()/success() and have
 * it surface without wiring per-page UI.
 */
@Component({
  selector: 'app-toast-stack',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    @if (notifications().length > 0) {
      <div class="toast-stack" role="status" aria-live="polite">
        @for (notification of notifications(); track notification.id) {
          <div class="toast" [attr.data-level]="notification.level">
            <span>{{ notification.message }}</span>
            <button type="button" class="toast__dismiss" (click)="dismiss(notification.id)" aria-label="Dismiss">
              &times;
            </button>
          </div>
        }
      </div>
    }
  `,
  styles: [
    `
      .toast-stack {
        position: fixed;
        bottom: var(--space-5);
        right: var(--space-5);
        display: flex;
        flex-direction: column;
        gap: var(--space-2);
        z-index: 100;
        max-width: 360px;
      }
      .toast {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: var(--space-3);
        padding: var(--space-3) var(--space-4);
        border-radius: var(--radius-md);
        background: var(--surface-raised);
        border: 1px solid var(--border-strong);
        box-shadow: var(--shadow-overlay);
        font-size: var(--text-sm);
        color: var(--ink-primary);
      }
      .toast[data-level='error'] {
        border-color: var(--status-failed);
        background: var(--status-failed-tint);
      }
      .toast[data-level='success'] {
        border-color: var(--status-processed);
        background: var(--status-processed-tint);
      }
      .toast__dismiss {
        background: none;
        border: none;
        cursor: pointer;
        font-size: var(--text-md);
        line-height: 1;
        color: inherit;
        padding: 0;
      }
    `,
  ],
})
export class ToastStackComponent {
  protected readonly notifications;

  constructor(private readonly notificationService: NotificationService) {
    this.notifications = this.notificationService.notifications;
  }

  dismiss(id: number): void {
    this.notificationService.dismiss(id);
  }
}
