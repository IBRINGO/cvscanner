import { ChangeDetectionStrategy, Component, DestroyRef, OnDestroy, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { NgIcon, provideIcons } from '@ng-icons/core';
import { CVSCANNER_ICONS } from '../../../../core/icons';
import { ApplicationProgressComponent, ApplicationStage } from '../../../../shared/components/ui/application-progress/application-progress.component';
import { DocumentPreviewComponent } from '../../../../shared/components/ui/document-preview/document-preview.component';
import { ProcessingTimelineComponent } from '../../../../shared/components/ui/processing-timeline/processing-timeline.component';
import { UploadDropzoneComponent } from '../../../../shared/components/ui/upload-dropzone/upload-dropzone.component';
import { DocumentSummary, ProcessingStatus } from '../../../../shared/models/document.model';
import { AnalysisApiService } from '../../../analysis/services/analysis-api.service';
import { CvApiService } from '../../../cvs/services/cv-api.service';
import { JobApiService } from '../../../jobs/services/job-api.service';
import { pollUntilDone } from '../../../../shared/utils/polling';

type JourneyStep = 'cv' | 'job';
type InputMode = 'text' | 'file';

const TERMINAL: ReadonlySet<ProcessingStatus> = new Set(['PROCESSED', 'FAILED']);
const AUTO_ADVANCE_DELAY_MS = 1400;

/**
 * The guided CV -> Job -> Analysis journey (section: "core user journey").
 * A candidate lands here to start a new application; each stage
 * auto-advances to the next on real, terminal backend status - never a
 * fabricated progress step. Existing standalone CV/Job library pages
 * are untouched; this is a separate entry point for the linear flow.
 */
@Component({
  selector: 'app-new-application-page',
  standalone: true,
  imports: [
    RouterLink,
    FormsModule,
    NgIcon,
    ApplicationProgressComponent,
    DocumentPreviewComponent,
    ProcessingTimelineComponent,
    UploadDropzoneComponent,
  ],
  viewProviders: [provideIcons(CVSCANNER_ICONS)],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="journey">
      <a routerLink="/workspace" class="journey__back text-secondary">
        <ng-icon name="lucideChevronRight" size="14" class="journey__back-icon" />
        Back to workspace
      </a>

      <app-application-progress [current]="progressStage()" [completed]="completedStages()" />

      @if (step() === 'cv') {
        <section class="journey__stage">
          @if (!cvDocument()) {
            <h1>Upload your CV</h1>
            <p class="text-secondary">
              CVScanner reads your document, structures it into a candidate profile, and keeps a
              record of exactly where each fact came from.
            </p>
            <app-upload-dropzone
              title="Drop your CV here"
              hint="PDF or DOCX, up to 10 MB"
              accept=".pdf,.docx"
              inputId="journey-cv-upload"
              (fileSelected)="onCvFileSelected($event)"
            />
            @if (cvUploading()) {
              <p class="journey__status text-secondary" role="status">Uploading...</p>
            }
          } @else {
            <div class="journey__document">
              <app-document-preview
                kind="cv"
                [heading]="cvDocument()!.original_filename"
                [filename]="cvDocument()!.original_filename"
                [status]="cvStatus() ?? cvDocument()!.status"
              />
              <div class="journey__document-detail">
                @if (!isTerminal(cvStatus())) {
                  <h2>Reading your document</h2>
                  <p class="text-secondary">This usually takes just a few seconds.</p>
                  <app-processing-timeline [status]="cvStatus() ?? 'UPLOADED'" />
                } @else if (cvStatus() === 'FAILED') {
                  <h2>We could not process this CV</h2>
                  <p class="text-secondary">{{ cvError() ?? 'An unexpected error occurred.' }}</p>
                  <button type="button" class="journey__retry" (click)="resetCv()">
                    Try a different file
                  </button>
                } @else {
                  <h2>Your CV is ready</h2>
                  <p class="text-secondary">Now let's see how it fits the job.</p>
                  <button type="button" class="journey__continue" (click)="goToJobNow()">
                    Continue to job offer
                    <ng-icon name="lucideArrowUpRight" size="14" />
                  </button>
                }
              </div>
            </div>
          }
        </section>
      } @else {
        <section class="journey__stage">
          @if (!jobDocument()) {
            <h1>Add the target job</h1>
            <p class="text-secondary">
              Paste the job description or upload the original file. CVScanner structures it into
              requirements to compare your CV against.
            </p>
            <div class="journey__toggle" role="tablist" aria-label="Job offer input method">
              <button
                type="button"
                role="tab"
                [attr.aria-selected]="jobMode() === 'text'"
                [attr.data-active]="jobMode() === 'text'"
                (click)="jobMode.set('text')"
              >
                Paste text
              </button>
              <button
                type="button"
                role="tab"
                [attr.aria-selected]="jobMode() === 'file'"
                [attr.data-active]="jobMode() === 'file'"
                (click)="jobMode.set('file')"
              >
                Upload file
              </button>
            </div>

            @if (jobMode() === 'text') {
              <label class="journey__field">
                <span class="text-secondary">Job description</span>
                <textarea
                  [(ngModel)]="jobText"
                  rows="10"
                  placeholder="Paste the full job posting here"
                ></textarea>
              </label>
              <button
                type="button"
                class="journey__submit"
                [disabled]="!jobText.trim() || jobSubmitting()"
                (click)="submitJobText()"
              >
                Structure this offer
              </button>
            } @else {
              <app-upload-dropzone
                title="Drop the job offer here"
                hint="PDF or DOCX, up to 10 MB"
                accept=".pdf,.docx"
                inputId="journey-job-upload"
                (fileSelected)="onJobFileSelected($event)"
              />
            }
            @if (jobSubmitting()) {
              <p class="journey__status text-secondary" role="status">Submitting...</p>
            }
          } @else {
            <div class="journey__document">
              <app-document-preview
                kind="job"
                [heading]="jobDocument()!.original_filename"
                [filename]="jobDocument()!.original_filename"
                [status]="jobStatus() ?? jobDocument()!.status"
              />
              <div class="journey__document-detail">
                @if (!isTerminal(jobStatus())) {
                  <h2>Reading the job offer</h2>
                  <p class="text-secondary">This usually takes just a few seconds.</p>
                  <app-processing-timeline [status]="jobStatus() ?? 'UPLOADED'" />
                } @else if (jobStatus() === 'FAILED') {
                  <h2>We could not process this job offer</h2>
                  <p class="text-secondary">{{ jobError() ?? 'An unexpected error occurred.' }}</p>
                  <button type="button" class="journey__retry" (click)="resetJob()">
                    Try again
                  </button>
                } @else if (creatingAnalysis()) {
                  <h2>Running your analysis</h2>
                  <p class="text-secondary">Comparing your CV against this job's requirements...</p>
                } @else if (analysisError()) {
                  <h2>We could not start the analysis</h2>
                  <p class="text-secondary">{{ analysisError() }}</p>
                  <button type="button" class="journey__retry" (click)="createAnalysis()">
                    Try again
                  </button>
                } @else {
                  <h2>Job offer ready</h2>
                  <p class="text-secondary">Starting the analysis now...</p>
                }
              </div>
            </div>
          }
        </section>
      }
    </div>
  `,
  styles: [
    `
      .journey {
        display: flex;
        flex-direction: column;
        gap: var(--space-6);
        max-width: 720px;
      }
      .journey__back {
        display: inline-flex;
        align-items: center;
        font-size: var(--text-sm);
        text-decoration: none;
        width: fit-content;
      }
      .journey__back-icon {
        transform: rotate(180deg);
        margin-right: var(--space-1);
      }
      .journey__stage {
        display: flex;
        flex-direction: column;
        gap: var(--space-4);
        animation: journey-fade var(--motion-slow) var(--motion-ease);
      }
      @keyframes journey-fade {
        from {
          opacity: 0;
          transform: translateY(6px);
        }
        to {
          opacity: 1;
          transform: translateY(0);
        }
      }
      .journey__status {
        font-size: var(--text-sm);
      }
      .journey__document {
        display: flex;
        gap: var(--space-6);
        align-items: flex-start;
        flex-wrap: wrap;
      }
      .journey__document-detail {
        flex: 1;
        min-width: 240px;
        display: flex;
        flex-direction: column;
        gap: var(--space-3);
      }
      .journey__continue,
      .journey__retry,
      .journey__submit {
        align-self: flex-start;
        display: inline-flex;
        align-items: center;
        gap: var(--space-2);
        border: none;
        background: var(--accent);
        color: #fff;
        padding: var(--space-3) var(--space-5);
        border-radius: var(--radius-sm);
        font-size: var(--text-sm);
        font-weight: 600;
        cursor: pointer;
      }
      .journey__submit:disabled {
        background: var(--border-strong);
        cursor: not-allowed;
      }
      .journey__retry {
        background: var(--negative);
      }
      .journey__toggle {
        display: inline-flex;
        gap: var(--space-1);
        background: var(--surface-sunken);
        padding: 2px;
        border-radius: var(--radius-pill);
        width: fit-content;
      }
      .journey__toggle button {
        border: none;
        background: transparent;
        padding: var(--space-2) var(--space-4);
        border-radius: var(--radius-pill);
        font-size: var(--text-sm);
        cursor: pointer;
        color: var(--ink-secondary);
      }
      .journey__toggle button[data-active='true'] {
        background: var(--surface-raised);
        color: var(--ink-primary);
        font-weight: 500;
      }
      .journey__field {
        display: flex;
        flex-direction: column;
        gap: var(--space-2);
      }
      .journey__field textarea {
        font-family: var(--font-mono);
        font-size: var(--text-sm);
        padding: var(--space-3);
        border: 1px solid var(--border-strong);
        border-radius: var(--radius-sm);
        background: var(--surface-raised);
        color: var(--ink-primary);
        resize: vertical;
      }
      .journey__field textarea:focus-visible {
        outline: 2px solid var(--accent);
        outline-offset: 1px;
      }

      @media (prefers-reduced-motion: reduce) {
        .journey__stage {
          animation: none;
        }
      }
    `,
  ],
})
export class NewApplicationComponent implements OnDestroy {
  // Public (not protected): the journey's state machine is exercised
  // directly in tests, matching this codebase's convention for
  // components whose behavior is more than template-display state.
  readonly step = signal<JourneyStep>('cv');

  readonly cvDocument = signal<DocumentSummary | null>(null);
  readonly cvStatus = signal<ProcessingStatus | null>(null);
  readonly cvError = signal<string | null>(null);
  readonly cvUploading = signal(false);

  readonly jobMode = signal<InputMode>('text');
  jobText = '';
  readonly jobDocument = signal<DocumentSummary | null>(null);
  readonly jobStatus = signal<ProcessingStatus | null>(null);
  readonly jobError = signal<string | null>(null);
  readonly jobSubmitting = signal(false);

  readonly creatingAnalysis = signal(false);
  readonly analysisError = signal<string | null>(null);

  private readonly destroyRef = inject(DestroyRef);
  private advanceTimeout: ReturnType<typeof setTimeout> | null = null;

  readonly progressStage = signal<ApplicationStage>('cv');
  readonly completedStages = signal<ApplicationStage[]>([]);

  constructor(
    private readonly cvApi: CvApiService,
    private readonly jobApi: JobApiService,
    private readonly analysisApi: AnalysisApiService,
    private readonly router: Router,
  ) {}

  ngOnDestroy(): void {
    if (this.advanceTimeout) clearTimeout(this.advanceTimeout);
  }

  isTerminal(status: ProcessingStatus | null): boolean {
    return status !== null && TERMINAL.has(status);
  }

  onCvFileSelected(file: File): void {
    this.cvUploading.set(true);
    this.cvApi.upload(file).subscribe({
      next: (document) => {
        this.cvUploading.set(false);
        this.cvDocument.set(document);
        this.cvStatus.set(document.status);
        this.pollCvStatus(document.id);
      },
      error: () => {
        this.cvUploading.set(false);
        this.cvError.set('The upload failed. Please try again.');
      },
    });
  }

  resetCv(): void {
    this.cvDocument.set(null);
    this.cvStatus.set(null);
    this.cvError.set(null);
  }

  goToJobNow(): void {
    if (this.advanceTimeout) clearTimeout(this.advanceTimeout);
    this.advanceToJob();
  }

  onJobFileSelected(file: File): void {
    this.jobSubmitting.set(true);
    this.jobApi.uploadFile(file).subscribe({
      next: (document) => this.handleJobCreated(document),
      error: () => {
        this.jobSubmitting.set(false);
        this.jobError.set('The upload failed. Please try again.');
      },
    });
  }

  submitJobText(): void {
    this.jobSubmitting.set(true);
    this.jobApi.uploadText(this.jobText).subscribe({
      next: (document) => this.handleJobCreated(document),
      error: () => {
        this.jobSubmitting.set(false);
        this.jobError.set('Submitting the job offer failed. Please try again.');
      },
    });
  }

  resetJob(): void {
    this.jobDocument.set(null);
    this.jobStatus.set(null);
    this.jobError.set(null);
    this.analysisError.set(null);
  }

  createAnalysis(): void {
    const cv = this.cvDocument();
    const job = this.jobDocument();
    if (!cv || !job) return;

    this.analysisError.set(null);
    this.creatingAnalysis.set(true);
    this.progressStage.set('analysis');
    this.analysisApi.createAnalysis(cv.id, job.id).subscribe({
      next: (analysis) => this.router.navigate(['/analysis', analysis.id]),
      error: () => {
        this.creatingAnalysis.set(false);
        this.analysisError.set('Starting the analysis failed. Please try again.');
      },
    });
  }

  private handleJobCreated(document: DocumentSummary): void {
    this.jobSubmitting.set(false);
    this.jobDocument.set(document);
    this.jobStatus.set(document.status);
    this.pollJobStatus(document.id);
  }

  private pollCvStatus(documentId: string): void {
    pollUntilDone(
      () => this.cvApi.getStatus(documentId),
      (response) => TERMINAL.has(response.status),
    )
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((response) => {
        this.cvStatus.set(response.status);
        if (response.status === 'FAILED') {
          this.cvError.set(response.error ?? 'An unexpected error occurred.');
        } else if (response.status === 'PROCESSED') {
          this.completedStages.set(['cv']);
          this.advanceTimeout = setTimeout(() => this.advanceToJob(), AUTO_ADVANCE_DELAY_MS);
        }
      });
  }

  private pollJobStatus(documentId: string): void {
    pollUntilDone(
      () => this.jobApi.getStatus(documentId),
      (response) => TERMINAL.has(response.status),
    )
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((response) => {
        this.jobStatus.set(response.status);
        if (response.status === 'FAILED') {
          this.jobError.set(response.error ?? 'An unexpected error occurred.');
        } else if (response.status === 'PROCESSED') {
          this.completedStages.set(['cv', 'job']);
          this.advanceTimeout = setTimeout(() => this.createAnalysis(), AUTO_ADVANCE_DELAY_MS);
        }
      });
  }

  private advanceToJob(): void {
    this.step.set('job');
    this.progressStage.set('job');
  }
}
