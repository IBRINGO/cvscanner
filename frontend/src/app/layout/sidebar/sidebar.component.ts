import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { NgIcon, provideIcons } from '@ng-icons/core';
import { CVSCANNER_ICONS } from '../../core/icons';
import { SidebarStateService } from './sidebar-state.service';

interface NavItem {
  label: string;
  path: string;
  icon: string;
}

const NAV_ITEMS: NavItem[] = [
  { label: 'Workspace', path: '/workspace', icon: 'lucideLayoutDashboard' },
  { label: 'Applications', path: '/applications', icon: 'lucideFolder' },
  { label: 'CV Library', path: '/cvs', icon: 'lucideFileText' },
  { label: 'Job Library', path: '/jobs', icon: 'lucideBriefcase' },
  { label: 'Templates', path: '/templates', icon: 'lucideLayers' },
  { label: 'Analysis', path: '/analysis', icon: 'lucideScanSearch' },
  { label: 'Recommendations', path: '/recommendations', icon: 'lucideListChecks' },
  { label: 'Tailoring', path: '/tailoring', icon: 'lucideGitBranch' },
  { label: 'Settings', path: '/settings', icon: 'lucideSettings' },
];

/**
 * The primary navigation. Desktop: collapsible (264px <-> 72px, state
 * remembered across visits) so the main content keeps most of the
 * visual attention once a candidate is deep in a document-editing
 * screen. Mobile: a slide-in drawer (triggered from the header's
 * hamburger button) rather than the desktop rail simply shrunk down.
 */
@Component({
  selector: 'app-sidebar',
  standalone: true,
  imports: [RouterLink, RouterLinkActive, NgIcon],
  viewProviders: [provideIcons(CVSCANNER_ICONS)],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    @if (state.mobileOpen()) {
      <div class="app-sidebar__backdrop" (click)="state.closeMobile()"></div>
    }

    <nav
      class="app-sidebar"
      aria-label="Main"
      [attr.data-collapsed]="state.collapsed()"
      [attr.data-mobile-open]="state.mobileOpen()"
    >
      <div class="app-sidebar__items">
        @for (item of navItems; track item.path) {
          <a
            [routerLink]="item.path"
            routerLinkActive="app-sidebar__link--active"
            class="app-sidebar__link"
            [title]="state.collapsed() ? item.label : ''"
            (click)="state.closeMobile()"
          >
            <span class="app-sidebar__active-bar" aria-hidden="true"></span>
            <ng-icon [name]="item.icon" size="18" />
            <span class="app-sidebar__label">{{ item.label }}</span>
          </a>
        }
      </div>

      <button
        type="button"
        class="app-sidebar__collapse"
        (click)="state.toggleCollapsed()"
        [attr.aria-label]="state.collapsed() ? 'Expand sidebar' : 'Collapse sidebar'"
      >
        <ng-icon name="lucideChevronsLeft" size="16" class="app-sidebar__collapse-icon" />
        <span class="app-sidebar__label">Collapse</span>
      </button>
    </nav>
  `,
  styles: [
    `
      .app-sidebar {
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        width: 264px;
        flex-shrink: 0;
        padding: var(--space-5) var(--space-3);
        border-right: 1px solid var(--border-subtle);
        background: var(--surface-raised);
        transition: width var(--motion-slow) var(--motion-ease);
        overflow: hidden;
      }
      .app-sidebar[data-collapsed='true'] {
        width: 72px;
      }
      .app-sidebar__items {
        display: flex;
        flex-direction: column;
        gap: 2px;
      }
      .app-sidebar__link {
        position: relative;
        display: flex;
        align-items: center;
        gap: var(--space-3);
        padding: var(--space-3);
        border-radius: var(--radius-sm);
        color: var(--ink-secondary);
        text-decoration: none;
        font-size: var(--text-sm);
        font-weight: 500;
        white-space: nowrap;
        transition: background var(--motion-fast) var(--motion-ease), color var(--motion-fast) var(--motion-ease);
      }
      .app-sidebar__active-bar {
        position: absolute;
        left: -12px;
        top: 8px;
        bottom: 8px;
        width: 3px;
        border-radius: var(--radius-pill);
        background: transparent;
      }
      .app-sidebar__link:hover {
        background: var(--surface-sunken);
        color: var(--ink-primary);
      }
      .app-sidebar__link--active {
        background: var(--accent-tint);
        color: var(--accent-strong);
        font-weight: 700;
      }
      .app-sidebar__link--active .app-sidebar__active-bar {
        background: var(--accent);
      }
      .app-sidebar__label {
        overflow: hidden;
        text-overflow: ellipsis;
      }
      .app-sidebar[data-collapsed='true'] .app-sidebar__link {
        justify-content: center;
        padding: var(--space-3) 0;
      }
      .app-sidebar[data-collapsed='true'] .app-sidebar__label {
        display: none;
      }
      .app-sidebar__collapse {
        display: flex;
        align-items: center;
        gap: var(--space-2);
        padding: var(--space-2) var(--space-3);
        border: none;
        background: none;
        color: var(--ink-tertiary);
        font: inherit;
        font-size: var(--text-xs);
        font-weight: 600;
        cursor: pointer;
        border-radius: var(--radius-sm);
        white-space: nowrap;
      }
      .app-sidebar__collapse:hover {
        background: var(--surface-sunken);
        color: var(--ink-primary);
      }
      .app-sidebar__collapse-icon {
        transition: transform var(--motion-base) var(--motion-ease);
        flex-shrink: 0;
      }
      .app-sidebar[data-collapsed='true'] .app-sidebar__collapse {
        justify-content: center;
      }
      .app-sidebar[data-collapsed='true'] .app-sidebar__collapse-icon {
        transform: rotate(180deg);
      }
      .app-sidebar__backdrop {
        display: none;
      }

      @media (prefers-reduced-motion: reduce) {
        .app-sidebar,
        .app-sidebar__collapse-icon {
          transition: none;
        }
      }

      @media (max-width: 767px) {
        .app-sidebar {
          position: fixed;
          inset: 0 25% 0 auto;
          z-index: 60;
          width: min(280px, 75vw);
          transform: translateX(100%);
          box-shadow: var(--shadow-overlay);
          transition: transform var(--motion-base) var(--motion-ease);
        }
        .app-sidebar[data-collapsed='true'] {
          width: min(280px, 75vw);
        }
        .app-sidebar[data-mobile-open='true'] {
          transform: translateX(0);
        }
        .app-sidebar[data-collapsed='true'] .app-sidebar__label {
          display: inline;
        }
        .app-sidebar[data-collapsed='true'] .app-sidebar__link {
          justify-content: flex-start;
          padding: var(--space-3);
        }
        .app-sidebar__backdrop {
          display: block;
          position: fixed;
          inset: 0;
          background: rgba(15, 23, 42, 0.4);
          z-index: 59;
        }
      }
    `,
  ],
})
export class SidebarComponent {
  protected readonly navItems = NAV_ITEMS;
  protected readonly state = inject(SidebarStateService);
}
