import { ChangeDetectionStrategy, Component, DestroyRef, OnInit, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { ProcessingTimelineComponent } from '../../../../shared/components/ui/processing-timeline/processing-timeline.component';
import { pollUntilDone } from '../../../../shared/utils/polling';
import { DocumentStatusResponse } from '../../../../shared/models/document.model';
import { CandidateProfileViewComponent } from '../../components/candidate-profile-view/candidate-profile-view.component';
import { CandidateProfile } from '../../models/candidate-profile.model';
import { CvApiService } from '../../services/cv-api.service';

const TERMINAL_STATUSES = new Set(['PROCESSED', 'FAILED']);

@Component({
  selector: 'app-cv-detail-page',
  standalone: true,
  imports: [ProcessingTimelineComponent, CandidateProfileViewComponent, RouterLink],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <a routerLink="/cvs" class="cv-detail__back text-secondary">Back to CVs</a>

    @if (status(); as current) {
      @if (!isDone(current.status)) {
        <section class="cv-detail__processing">
          <h1>Reading your document</h1>
          <p class="text-secondary">This usually takes just a few seconds.</p>
          <app-processing-timeline [status]="current.status" />
        </section>
      } @else if (current.status === 'FAILED') {
        <section class="cv-detail__error">
          <h1>We could not process this document</h1>
          <p class="text-secondary">{{ current.error ?? 'An unexpected error occurred.' }}</p>
        </section>
      } @else if (profile()) {
        <app-candidate-profile-view [profile]="profile()!" />
      }
    }
  `,
  styles: [
    `
      .cv-detail__back {
        display: inline-block;
        margin-bottom: var(--space-5);
        font-size: var(--text-sm);
        text-decoration: none;
      }
      .cv-detail__processing,
      .cv-detail__error {
        display: flex;
        flex-direction: column;
        gap: var(--space-4);
        max-width: 560px;
      }
    `,
  ],
})
export class CvDetailComponent implements OnInit {
  protected readonly status = signal<DocumentStatusResponse | null>(null);
  protected readonly profile = signal<CandidateProfile | null>(null);

  private readonly route = inject(ActivatedRoute);
  private readonly destroyRef = inject(DestroyRef);

  constructor(private readonly cvApi: CvApiService) {}

  ngOnInit(): void {
    const documentId = this.route.snapshot.paramMap.get('id');
    if (!documentId) return;

    pollUntilDone(
      () => this.cvApi.getStatus(documentId),
      (response) => TERMINAL_STATUSES.has(response.status),
    )
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((response) => {
        this.status.set(response);
        if (response.status === 'PROCESSED') {
          this.cvApi.getProfile(documentId).subscribe((profileResponse) => {
            this.profile.set(profileResponse.profile);
          });
        }
      });
  }

  isDone(status: string): boolean {
    return TERMINAL_STATUSES.has(status);
  }
}
