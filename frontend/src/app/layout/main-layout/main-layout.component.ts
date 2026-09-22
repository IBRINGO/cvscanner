import { ChangeDetectionStrategy, Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { ToastStackComponent } from '../../shared/components/ui/toast-stack/toast-stack.component';
import { FooterComponent } from '../footer/footer.component';
import { HeaderComponent } from '../header/header.component';
import { SidebarComponent } from '../sidebar/sidebar.component';

@Component({
  selector: 'app-main-layout',
  standalone: true,
  imports: [RouterOutlet, HeaderComponent, SidebarComponent, FooterComponent, ToastStackComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="app-shell">
      <app-header />
      <div class="app-shell__body">
        <app-sidebar />
        <main class="app-shell__content">
          <router-outlet />
        </main>
      </div>
      <app-footer />
    </div>
    <app-toast-stack />
  `,
  styles: [
    `
      .app-shell {
        display: flex;
        flex-direction: column;
        min-height: 100dvh;
      }
      .app-shell__body {
        display: flex;
        flex: 1;
      }
      .app-shell__content {
        flex: 1;
        min-width: 0;
        padding: var(--space-6);
      }

      @media (max-width: 767px) {
        .app-shell__body {
          flex-direction: column;
        }
        .app-shell__content {
          padding: var(--space-4);
        }
      }
    `,
  ],
})
export class MainLayoutComponent {}
