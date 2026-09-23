import { ChangeDetectionStrategy, Component, DestroyRef, OnInit, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { NgIcon, provideIcons } from '@ng-icons/core';
import { CVSCANNER_ICONS } from '../../../../core/icons';
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
  imports: [ProcessingTimelineComponent, JobProfileViewComponent, RouterLink, NgIcon],
  viewProviders: [provideIcons(CVSCANNER_ICONS)],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <a routerLink="/jobs" class="job-detail__back">
      <ng-icon name="lucideArrowLeft" size="15" />
      Back to job offers
    </a>

    @if (status(); as current) {
      @if (!isDone(current.status)) {
        <section class="job-detail__processing">
          <h1>Reading this offer</h1>
          <p class="text-secondary">This usually takes just a few seconds.</p>
          <app-processing-timeline [status]="current.status" />
        </section>
      } @else if (current.status === 'FAILED') {
        <section class="job-detail__error">
          <span class="job-detail__error-icon" aria-hidden="true">
            <ng-icon name="lucideTriangleAlert" size="20" />
          </span>
          <div>
            <h1>We could not process this offer</h1>
            <p class="text-secondary">{{ current.error ?? 'An unexpected error occurred.' }}</p>
          </div>
        </section>
      } @else if (profile()) {
        <app-job-profile-view [profile]="profile()!" />
      }
    }
  `,
  styles: [
    `
      .job-detail__back {
        display: inline-flex;
        align-items: center;
        gap: var(--space-1);
        margin-bottom: var(--space-5);
        font-size: var(--text-sm);
        font-weight: 500;
        color: var(--ink-secondary);
        text-decoration: none;
        transition: color var(--motion-fast) var(--motion-ease);
      }
      .job-detail__back:hover {
        color: var(--accent);
      }
      .job-detail__processing {
        display: flex;
        flex-direction: column;
        gap: var(--space-4);
        max-width: 560px;
        padding: var(--space-6);
        background: var(--surface-raised);
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-lg);
        box-shadow: var(--shadow-document);
      }
      .job-detail__error {
        display: flex;
        align-items: flex-start;
        gap: var(--space-3);
        max-width: 560px;
        padding: var(--space-6);
        background: var(--negative-tint);
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-lg);
      }
      .job-detail__error-icon {
        flex-shrink: 0;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 36px;
        height: 36px;
        border-radius: var(--radius-pill);
        background: var(--surface-raised);
        color: var(--negative);
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
