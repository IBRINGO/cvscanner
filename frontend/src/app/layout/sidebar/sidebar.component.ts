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
    <nav class="app-sidebar">
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
        padding: 1rem 0.5rem;
        border-right: 1px solid var(--color-border, #d0d5dd);
      }
      .app-sidebar__link {
        padding: 0.5rem 0.75rem;
        border-radius: 6px;
        color: inherit;
        text-decoration: none;
      }
      .app-sidebar__link:hover {
        background: var(--color-muted-bg, #f2f4f7);
      }
      .app-sidebar__link--active {
        background: var(--color-muted-bg, #f2f4f7);
        font-weight: 600;
      }
    `,
  ],
})
export class SidebarComponent {
  protected readonly navItems = NAV_ITEMS;
}
