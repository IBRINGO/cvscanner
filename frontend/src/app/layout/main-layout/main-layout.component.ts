import { ChangeDetectionStrategy, Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { FooterComponent } from '../footer/footer.component';
import { HeaderComponent } from '../header/header.component';
import { SidebarComponent } from '../sidebar/sidebar.component';

@Component({
  selector: 'app-main-layout',
  standalone: true,
  imports: [RouterOutlet, HeaderComponent, SidebarComponent, FooterComponent],
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
  `,
  styles: [
    `
      .app-shell {
        display: flex;
        flex-direction: column;
        min-height: 100vh;
      }
      .app-shell__body {
        display: flex;
        flex: 1;
      }
      .app-shell__content {
        flex: 1;
        padding: 1.5rem;
      }
    `,
  ],
})
export class MainLayoutComponent {}
