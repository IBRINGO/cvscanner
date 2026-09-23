import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { NgIcon, provideIcons } from '@ng-icons/core';
import { CVSCANNER_ICONS } from '../../core/icons';
import { isLoading } from '../../core/http/loading.interceptor';
import { SidebarStateService } from '../sidebar/sidebar-state.service';

/**
 * The brand mark is the real CVScanner logo artwork (cropped to just the
 * icon glyph - see docs/images/logo/cvscanner-logo.png for the full
 * lockup), not a synthetic gradient badge. It anchors the brand identity
 * everywhere the header appears.
 */
@Component({
  selector: 'app-header',
  standalone: true,
  imports: [NgIcon, RouterLink],
  viewProviders: [provideIcons(CVSCANNER_ICONS)],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <header class="app-header">
      <div class="app-header__left">
        <button
          type="button"
          class="app-header__menu-trigger"
          aria-label="Open navigation"
          (click)="sidebarState.openMobile()"
        >
          <ng-icon name="lucideMenu" size="20" />
        </button>
        <a routerLink="/workspace" class="app-header__brand">
          <span class="app-header__mark">
            <img src="/images/cvscanner-icon.png" alt="" />
          </span>
          CVScanner
        </a>
      </div>
      <div class="app-header__right">
        @if (isLoading()) {
          <span class="app-header__status" role="status">
            <span class="app-header__status-dot" aria-hidden="true"></span>
            Working
          </span>
        }
        <a routerLink="/applications/new" class="app-header__cta">
          <ng-icon name="lucideSparkles" size="15" />
          <span>Start an application</span>
        </a>
      </div>
    </header>
  `,
  styles: [
    `
      .app-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        height: 64px;
        padding: 0 var(--space-6);
        border-bottom: 1px solid var(--border-subtle);
        background: var(--surface-raised);
      }
      .app-header__left {
        display: flex;
        align-items: center;
        gap: var(--space-3);
      }
      .app-header__menu-trigger {
        display: none;
        align-items: center;
        justify-content: center;
        width: 36px;
        height: 36px;
        border: none;
        background: none;
        color: var(--ink-secondary);
        cursor: pointer;
        border-radius: var(--radius-sm);
        flex-shrink: 0;
        margin-left: calc(var(--space-2) * -1);
      }
      .app-header__menu-trigger:hover {
        background: var(--surface-sunken);
        color: var(--ink-primary);
      }
      .app-header__brand {
        display: inline-flex;
        align-items: center;
        gap: var(--space-2);
        font-family: var(--font-display);
        font-weight: 600;
        font-size: var(--text-lg);
        color: var(--ink-primary);
        letter-spacing: -0.01em;
        text-decoration: none;
      }
      .app-header__mark {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 32px;
        height: 32px;
        padding: 3px;
        border-radius: var(--radius-sm);
        background: #fff;
        flex-shrink: 0;
      }
      .app-header__mark img {
        width: 100%;
        height: 100%;
        object-fit: contain;
      }
      .app-header__right {
        display: flex;
        align-items: center;
        gap: var(--space-4);
      }
      .app-header__status {
        display: inline-flex;
        align-items: center;
        gap: var(--space-2);
        padding: var(--space-1) var(--space-3);
        border-radius: var(--radius-pill);
        background: var(--accent-tint);
        font-size: var(--text-sm);
        font-weight: 500;
        color: var(--accent-strong);
      }
      .app-header__status-dot {
        width: 6px;
        height: 6px;
        border-radius: 50%;
        background: var(--accent);
        animation: app-header-pulse 1.4s var(--motion-ease) infinite;
      }
      .app-header__cta {
        display: inline-flex;
        align-items: center;
        gap: var(--space-2);
        padding: var(--space-2) var(--space-4);
        border-radius: var(--radius-pill);
        background: var(--accent);
        color: #fff;
        font-size: var(--text-sm);
        font-weight: 600;
        text-decoration: none;
        white-space: nowrap;
        transition:
          background var(--motion-fast) var(--motion-ease),
          transform var(--motion-fast) var(--motion-ease),
          box-shadow var(--motion-fast) var(--motion-ease);
      }
      .app-header__cta:hover {
        background: var(--accent-strong);
        transform: translateY(-1px);
        box-shadow: var(--shadow-document);
      }

      @keyframes app-header-pulse {
        0%,
        100% {
          transform: scale(1);
          opacity: 1;
        }
        50% {
          transform: scale(1.5);
          opacity: 0.6;
        }
      }

      @media (prefers-reduced-motion: reduce) {
        .app-header__cta {
          transition: none;
        }
        .app-header__status-dot {
          animation: none;
        }
      }

      @media (max-width: 767px) {
        .app-header {
          padding: 0 var(--space-4);
        }
        .app-header__menu-trigger {
          display: inline-flex;
        }
        .app-header__cta span {
          display: none;
        }
        .app-header__cta {
          padding: var(--space-2);
        }
      }
    `,
  ],
})
export class HeaderComponent {
  protected readonly isLoading = isLoading;
  protected readonly sidebarState = inject(SidebarStateService);
}
