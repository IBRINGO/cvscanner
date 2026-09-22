import { ChangeDetectionStrategy, Component } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';

interface NavItem {
  label: string;
  path: string;
}

const NAV_ITEMS: NavItem[] = [
  { label: 'Dashboard', path: '/dashboard' },
  { label: 'CVs', path: '/cvs' },
  { label: 'Jobs', path: '/jobs' },
  { label: 'Analysis', path: '/analysis' },
  { label: 'Recommendations', path: '/recommendations' },
  { label: 'Tailoring', path: '/tailoring' },
  { label: 'Applications', path: '/applications' },
  { label: 'Settings', path: '/settings' },
];

@Component({
  selector: 'app-sidebar',
  standalone: true,
  imports: [RouterLink, RouterLinkActive],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <nav class="app-sidebar" aria-label="Main">
      @for (item of navItems; track item.path) {
        <a
          [routerLink]="item.path"
          routerLinkActive="app-sidebar__link--active"
          class="app-sidebar__link"
        >
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
        border-right: 1px solid var(--border-subtle);
        background: var(--surface-raised);
      }
      .app-sidebar__link {
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
        font-weight: 500;
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
