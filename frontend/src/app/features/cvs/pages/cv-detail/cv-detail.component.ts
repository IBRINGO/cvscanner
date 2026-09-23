import { ChangeDetectionStrategy, Component, DestroyRef, OnInit, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { NgIcon, provideIcons } from '@ng-icons/core';
import { CVSCANNER_ICONS } from '../../../../core/icons';
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
  imports: [ProcessingTimelineComponent, CandidateProfileViewComponent, RouterLink, NgIcon],
  viewProviders: [provideIcons(CVSCANNER_ICONS)],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <a routerLink="/cvs" class="cv-detail__back">
      <ng-icon name="lucideArrowLeft" size="15" />
      Back to CVs
    </a>

    @if (status(); as current) {
      @if (!isDone(current.status)) {
        <section class="cv-detail__processing">
          <h1>Reading your document</h1>
          <p class="text-secondary">This usually takes just a few seconds.</p>
          <app-processing-timeline [status]="current.status" />
        </section>
      } @else if (current.status === 'FAILED') {
        <section class="cv-detail__error">
          <span class="cv-detail__error-icon" aria-hidden="true">
            <ng-icon name="lucideTriangleAlert" size="20" />
          </span>
          <div>
            <h1>We could not process this document</h1>
            <p class="text-secondary">{{ current.error ?? 'An unexpected error occurred.' }}</p>
          </div>
        </section>
      } @else if (profile()) {
        <a [routerLink]="['/cvs', documentId, 'editor']" class="cv-detail__editor-link">
          <ng-icon name="lucideSparkles" size="15" />
          Open in CV editor
          <ng-icon name="lucideArrowUpRight" size="14" />
        </a>
        <app-candidate-profile-view [profile]="profile()!" />
      }
    }
  `,
  styles: [
    `
      .cv-detail__back {
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
      .cv-detail__back:hover {
        color: var(--accent);
      }
      .cv-detail__processing {
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
      .cv-detail__error {
        display: flex;
        align-items: flex-start;
        gap: var(--space-3);
        max-width: 560px;
        padding: var(--space-6);
        background: var(--negative-tint);
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-lg);
      }
      .cv-detail__error-icon {
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
      .cv-detail__editor-link {
        display: inline-flex;
        align-items: center;
        gap: var(--space-2);
        margin-bottom: var(--space-5);
        padding: var(--space-2) var(--space-4);
        border-radius: var(--radius-sm);
        background: var(--accent);
        color: #fff;
        font-size: var(--text-sm);
        font-weight: 600;
        text-decoration: none;
        transition:
          background var(--motion-fast) var(--motion-ease),
          transform var(--motion-fast) var(--motion-ease);
      }
      .cv-detail__editor-link:hover {
        background: var(--accent-strong);
        transform: translateY(-1px);
      }
    `,
  ],
})
export class CvDetailComponent implements OnInit {
  protected readonly status = signal<DocumentStatusResponse | null>(null);
  protected readonly profile = signal<CandidateProfile | null>(null);
  protected documentId = '';

  private readonly route = inject(ActivatedRoute);
  private readonly destroyRef = inject(DestroyRef);

  constructor(private readonly cvApi: CvApiService) {}

  ngOnInit(): void {
    const documentId = this.route.snapshot.paramMap.get('id');
    if (!documentId) return;
    this.documentId = documentId;

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
