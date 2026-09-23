import { ChangeDetectionStrategy, Component } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { NgIcon, provideIcons } from '@ng-icons/core';
import { CVSCANNER_ICONS } from '../../core/icons';

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
  { label: 'Analysis', path: '/analysis', icon: 'lucideScanSearch' },
  { label: 'Recommendations', path: '/recommendations', icon: 'lucideListChecks' },
  { label: 'Tailoring', path: '/tailoring', icon: 'lucideGitBranch' },
  { label: 'Settings', path: '/settings', icon: 'lucideSettings' },
];

@Component({
  selector: 'app-sidebar',
  standalone: true,
  imports: [RouterLink, RouterLinkActive, NgIcon],
  viewProviders: [provideIcons(CVSCANNER_ICONS)],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <nav class="app-sidebar" aria-label="Main">
      @for (item of navItems; track item.path) {
        <a
          [routerLink]="item.path"
          routerLinkActive="app-sidebar__link--active"
          class="app-sidebar__link"
        >
          <ng-icon [name]="item.icon" size="16" />
          {{ item.label }}
        </a>
      }
    </nav>
  `,
  styles: [
    `
      .app-sidebar {
        display: flex;
        flex-direction: column;
        width: 220px;
        flex-shrink: 0;
        padding: var(--space-5) var(--space-3);
        gap: 2px;
        border-right: 1px solid var(--border-subtle);
        background: var(--surface-raised);
      }
      .app-sidebar__link {
        display: flex;
        align-items: center;
        gap: var(--space-2);
        padding: var(--space-2) var(--space-3);
        border-radius: var(--radius-sm);
        color: var(--ink-secondary);
        text-decoration: none;
        font-size: var(--text-sm);
        transition: background var(--motion-fast) var(--motion-ease), color var(--motion-fast) var(--motion-ease);
      }
      .app-sidebar__link:hover {
        background: var(--surface-sunken);
        color: var(--ink-primary);
      }
      .app-sidebar__link--active {
        background: var(--accent-tint);
        color: var(--accent-strong);
        font-weight: 600;
      }

      @media (max-width: 767px) {
        .app-sidebar {
          width: 100%;
          min-width: 0;
          flex-direction: row;
          overflow-x: auto;
          border-right: none;
          border-bottom: 1px solid var(--border-subtle);
          padding: var(--space-2);
        }
        .app-sidebar__link {
          white-space: nowrap;
        }
      }
    `,
  ],
})
export class SidebarComponent {
  protected readonly navItems = NAV_ITEMS;
}
