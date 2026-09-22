import { ChangeDetectionStrategy, Component } from '@angular/core';
import { HealthStatusComponent } from '../../components/health-status/health-status.component';

@Component({
  selector: 'app-dashboard-page',
  standalone: true,
  imports: [HealthStatusComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <section class="dashboard-page">
      <h1>Dashboard</h1>
      <p>Welcome to CVScanner. This page will grow into an activity overview in a later phase.</p>
      <app-health-status />
    </section>
  `,
  styles: [
    `
      .dashboard-page {
        display: flex;
        flex-direction: column;
        gap: 1rem;
        max-width: 640px;
      }
    `,
  ],
})
export class DashboardPageComponent {}
