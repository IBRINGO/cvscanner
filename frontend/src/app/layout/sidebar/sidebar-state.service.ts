import { Injectable, signal } from '@angular/core';

const STORAGE_KEY = 'cvscanner.sidebar.collapsed';

/**
 * Shared collapse/mobile-open state for the sidebar, injected by both
 * the header (which owns the collapse/hamburger triggers) and the
 * sidebar itself. Collapsed state is remembered across visits; mobile
 * open state is always session-local (never persisted, always starts
 * closed).
 */
@Injectable({ providedIn: 'root' })
export class SidebarStateService {
  private readonly _collapsed = signal(this.readPersisted());
  readonly collapsed = this._collapsed.asReadonly();
  readonly mobileOpen = signal(false);

  toggleCollapsed(): void {
    const next = !this._collapsed();
    this._collapsed.set(next);
    this.persist(next);
  }

  openMobile(): void {
    this.mobileOpen.set(true);
  }

  closeMobile(): void {
    this.mobileOpen.set(false);
  }

  private readPersisted(): boolean {
    try {
      return localStorage.getItem(STORAGE_KEY) === 'true';
    } catch {
      return false;
    }
  }

  private persist(value: boolean): void {
    try {
      localStorage.setItem(STORAGE_KEY, String(value));
    } catch {
      // Storage unavailable (private browsing, quota) - collapse state
      // simply won't survive a reload; not worth failing over.
    }
  }
}
