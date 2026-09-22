import { DatePipe } from '@angular/common';
import { ChangeDetectionStrategy, Component, OnInit, signal } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { StatusBadgeComponent } from '../../../../shared/components/ui/status-badge/status-badge.component';
import { UploadDropzoneComponent } from '../../../../shared/components/ui/upload-dropzone/upload-dropzone.component';
import { DocumentSummary } from '../../../../shared/models/document.model';
import { CvApiService } from '../../services/cv-api.service';

const PIPELINE_STEPS = [
  'Your file is stored and a text extraction pass begins',
  'Sections such as Experience, Education, and Skills are detected',
  'A structured candidate profile is built, fact by fact',
  'Skills are matched against the CVScanner taxonomy where possible',
];

/**
 * The CV workspace: a split layout (upload on the left, your documents
 * on the right) rather than a dashboard of cards - see section 67.
 */
@Component({
  selector: 'app-cv-list-page',
  standalone: true,
  imports: [UploadDropzoneComponent, StatusBadgeComponent, RouterLink, DatePipe],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <section class="cv-workspace">
      <div class="cv-workspace__upload">
        <h1>Upload a CV</h1>
        <p class="text-secondary">
          CVScanner reads your document, structures it into a candidate profile, and keeps a
          record of exactly where each fact came from.
        </p>

        <app-upload-dropzone
          title="Drop your CV here"
          hint="PDF or DOCX, up to 10 MB"
          accept=".pdf,.docx"
          inputId="cv-upload-input"
          (fileSelected)="onFileSelected($event)"
        />

        @if (uploading()) {
          <p class="cv-workspace__uploading" role="status">Uploading...</p>
        }

        <div class="cv-workspace__pipeline">
          <h2>What happens next</h2>
          <ol>
            @for (step of pipelineSteps; track step) {
              <li>{{ step }}</li>
            }
          </ol>
        </div>
      </div>

      <div class="cv-workspace__list">
        <h2>Your CVs</h2>
        @if (documents().length === 0) {
          <p class="text-secondary">Nothing uploaded yet. Your CVs will appear here.</p>
        } @else {
          <ul class="document-index">
            @for (document of documents(); track document.id) {
              <li class="document-index__row">
                <a [routerLink]="['/cvs', document.id]" class="document-index__link">
                  <span class="document-index__name">{{ document.original_filename }}</span>
                  <span class="document-index__meta text-tertiary font-mono">{{
                    document.created_at | date: 'mediumDate'
                  }}</span>
                </a>
                <app-status-badge [status]="document.status" />
              </li>
            }
          </ul>
        }
      </div>
    </section>
  `,
  styles: [
    `
      .cv-workspace {
        display: grid;
        grid-template-columns: minmax(0, 1.1fr) minmax(0, 0.9fr);
        gap: var(--space-7);
        align-items: start;
      }
      .cv-workspace__upload {
        display: flex;
        flex-direction: column;
        gap: var(--space-4);
      }
      .cv-workspace__uploading {
        color: var(--accent);
        font-size: var(--text-sm);
      }
      .cv-workspace__pipeline {
        margin-top: var(--space-4);
      }
      .cv-workspace__pipeline ol {
        padding-left: var(--space-5);
        color: var(--ink-secondary);
        font-size: var(--text-sm);
        display: flex;
        flex-direction: column;
        gap: var(--space-2);
      }
      .cv-workspace__list h2 {
        margin-bottom: var(--space-4);
      }
      .document-index {
        list-style: none;
        margin: 0;
        padding: 0;
        border-top: 1px solid var(--border-subtle);
      }
      .document-index__row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: var(--space-3);
        padding: var(--space-3) 0;
        border-bottom: 1px solid var(--border-subtle);
      }
      .document-index__link {
        display: flex;
        flex-direction: column;
        gap: 2px;
        text-decoration: none;
        min-width: 0;
      }
      .document-index__name {
        color: var(--ink-primary);
        font-weight: 500;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }
      .document-index__meta {
        font-size: var(--text-xs);
      }

      @media (max-width: 900px) {
        .cv-workspace {
          grid-template-columns: minmax(0, 1fr);
        }
      }
    `,
  ],
})
export class CvListComponent implements OnInit {
  protected readonly pipelineSteps = PIPELINE_STEPS;
  protected readonly documents = signal<DocumentSummary[]>([]);
  protected readonly uploading = signal(false);

  constructor(
    private readonly cvApi: CvApiService,
    private readonly router: Router,
  ) {}

  ngOnInit(): void {
    this.refresh();
  }

  onFileSelected(file: File): void {
    this.uploading.set(true);
    this.cvApi.upload(file).subscribe({
      next: (document) => {
        this.uploading.set(false);
        this.router.navigate(['/cvs', document.id]);
      },
      error: () => {
        this.uploading.set(false);
      },
    });
  }

  private refresh(): void {
    this.cvApi.list().subscribe((documents) => this.documents.set(documents));
  }
}
