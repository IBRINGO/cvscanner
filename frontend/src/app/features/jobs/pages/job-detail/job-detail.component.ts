import { ChangeDetectionStrategy, Component, DestroyRef, OnInit, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { ProcessingTimelineComponent } from '../../../../shared/components/ui/processing-timeline/processing-timeline.component';
import { DocumentStatusResponse } from '../../../../shared/models/document.model';
import { pollUntilDone } from '../../../../shared/utils/polling';
import { JobProfileViewComponent } from '../../components/job-profile-view/job-profile-view.component';
import { JobProfile } from '../../models/job-profile.model';
import { JobApiService } from '../../services/job-api.service';

const TERMINAL_STATUSES = new Set(['PROCESSED', 'FAILED']);

@Component({
  selector: 'app-job-detail-page',
  standalone: true,
  imports: [ProcessingTimelineComponent, JobProfileViewComponent, RouterLink],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <a routerLink="/jobs" class="job-detail__back text-secondary">Back to job offers</a>

    @if (status(); as current) {
      @if (!isDone(current.status)) {
        <section class="job-detail__processing">
          <h1>Reading this offer</h1>
          <p class="text-secondary">This usually takes just a few seconds.</p>
          <app-processing-timeline [status]="current.status" />
        </section>
      } @else if (current.status === 'FAILED') {
        <section class="job-detail__error">
          <h1>We could not process this offer</h1>
          <p class="text-secondary">{{ current.error ?? 'An unexpected error occurred.' }}</p>
        </section>
      } @else if (profile()) {
        <app-job-profile-view [profile]="profile()!" />
      }
    }
  `,
  styles: [
    `
      .job-detail__back {
        display: inline-block;
        margin-bottom: var(--space-5);
        font-size: var(--text-sm);
        text-decoration: none;
      }
      .job-detail__processing,
      .job-detail__error {
        display: flex;
        flex-direction: column;
        gap: var(--space-4);
        max-width: 560px;
      }
    `,
  ],
})
export class JobDetailComponent implements OnInit {
  protected readonly status = signal<DocumentStatusResponse | null>(null);
  protected readonly profile = signal<JobProfile | null>(null);

  private readonly route = inject(ActivatedRoute);
  private readonly destroyRef = inject(DestroyRef);

  constructor(private readonly jobApi: JobApiService) {}

  ngOnInit(): void {
    const documentId = this.route.snapshot.paramMap.get('id');
    if (!documentId) return;

    pollUntilDone(
      () => this.jobApi.getStatus(documentId),
      (response) => TERMINAL_STATUSES.has(response.status),
    )
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((response) => {
        this.status.set(response);
        if (response.status === 'PROCESSED') {
          this.jobApi.getProfile(documentId).subscribe((profileResponse) => {
            this.profile.set(profileResponse.profile);
          });
        }
      });
  }

  isDone(status: string): boolean {
    return TERMINAL_STATUSES.has(status);
  }
}
