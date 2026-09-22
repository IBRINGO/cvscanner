import { Injectable, signal } from '@angular/core';

export type NotificationLevel = 'info' | 'success' | 'error';

export interface Notification {
  id: number;
  level: NotificationLevel;
  message: string;
}

let nextId = 1;

/**
 * Minimal app-wide notification (toast) store. UI presentation (e.g. a
 * toast component in shared/components/ui) reads `notifications()` and
 * calls `dismiss()`; this service only owns the state.
 */
@Injectable({ providedIn: 'root' })
export class NotificationService {
  private readonly _notifications = signal<Notification[]>([]);
  readonly notifications = this._notifications.asReadonly();

  info(message: string): void {
    this.push('info', message);
  }

  success(message: string): void {
    this.push('success', message);
  }

  error(message: string): void {
    this.push('error', message);
  }

  dismiss(id: number): void {
    this._notifications.update((list) => list.filter((n) => n.id !== id));
  }

  private push(level: NotificationLevel, message: string): void {
    const notification: Notification = { id: nextId++, level, message };
    this._notifications.update((list) => [...list, notification]);
  }
}
