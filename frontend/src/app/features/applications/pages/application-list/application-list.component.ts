import { ChangeDetectionStrategy, Component, OnInit, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { forkJoin } from 'rxjs';
import { AnalysisApiService } from '../../../analysis/services/analysis-api.service';
import { CvApiService } from '../../../cvs/services/cv-api.service';
import { JobApiService } from '../../../jobs/services/job-api.service';
import { TailoringApiService } from '../../../tailoring/services/tailoring-api.service';
import { ApplicationCardComponent } from '../../components/application-card/application-card.component';
import { ApplicationView } from '../../models/application.model';
import { buildApplications } from '../../utils/build-applications';

/**
 * The full applications index (every CV+job pairing that has an
 * analysis behind it, not just the active/recent ones the Workspace
 * home surfaces). Same derived-join logic as the Workspace page - see
 * build-applications.ts.
 */
@Component({
  selector: 'app-application-list-page',
  standalone: true,
  imports: [RouterLink, ApplicationCardComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <section class="applications">
      <header class="applications__header">
        <h1>Applications</h1>
        <p class="text-secondary">Every CV and job offer pairing you've analyzed.</p>
      </header>

      @if (loading()) {
        <p class="text-secondary">Loading applications...</p>
      } @else if (applications().length === 0) {
        <p class="text-secondary">
          No applications yet.
          <a routerLink="/applications/new">Analyze your first one.</a>
        </p>
      } @else {
        <div class="applications__list">
          @for (app of applications(); track app.analysisId) {
            <app-application-card [app]="app" />
          }
        </div>
      }
    </section>
  `,
  styles: [
    `
      .applications {
        display: flex;
        flex-direction: column;
        gap: var(--space-5);
        max-width: 760px;
      }
      .applications__header {
        display: flex;
        flex-direction: column;
        gap: var(--space-1);
      }
      .applications__list {
        display: flex;
        flex-direction: column;
        gap: var(--space-3);
      }
    `,
  ],
})
export class ApplicationListComponent implements OnInit {
  protected readonly applications = signal<ApplicationView[]>([]);
  protected readonly loading = signal(true);

  constructor(
    private readonly cvApi: CvApiService,
    private readonly jobApi: JobApiService,
    private readonly analysisApi: AnalysisApiService,
    private readonly tailoringApi: TailoringApiService,
  ) {}

  ngOnInit(): void {
    forkJoin({
      cvs: this.cvApi.list(),
      jobs: this.jobApi.list(),
      analyses: this.analysisApi.list(),
      tailoringPlans: this.tailoringApi.list(),
    }).subscribe({
      next: ({ cvs, jobs, analyses, tailoringPlans }) => {
        this.applications.set(buildApplications(cvs, jobs, analyses, tailoringPlans));
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }
}
