import { DatePipe } from '@angular/common';
import { ChangeDetectionStrategy, Component, OnInit, signal } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { NgIcon, provideIcons } from '@ng-icons/core';
import { CVSCANNER_ICONS } from '../../../../core/icons';
import { StatusBadgeComponent } from '../../../../shared/components/ui/status-badge/status-badge.component';
import { UploadDropzoneComponent } from '../../../../shared/components/ui/upload-dropzone/upload-dropzone.component';
import { DocumentSummary } from '../../../../shared/models/document.model';
import { CvApiService } from '../../services/cv-api.service';

interface PipelineStep {
  icon: string;
  text: string;
}

const PIPELINE_STEPS: PipelineStep[] = [
  { icon: 'lucideFileUp', text: 'Your file is stored and a text extraction pass begins' },
  { icon: 'lucideLayers', text: 'Sections such as Experience, Education, and Skills are detected' },
  { icon: 'lucideFileCheck', text: 'A structured candidate profile is built, fact by fact' },
  { icon: 'lucideNetwork', text: 'Skills are matched against the CVScanner taxonomy where possible' },
];

/**
 * The CV workspace: a split layout (upload on the left, your documents
 * on the right) rather than a dashboard of cards - see section 67.
 */
@Component({
  selector: 'app-cv-list-page',
  standalone: true,
  imports: [UploadDropzoneComponent, StatusBadgeComponent, RouterLink, DatePipe, NgIcon],
  viewProviders: [provideIcons(CVSCANNER_ICONS)],
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
          <ol class="pipeline">
            @for (step of pipelineSteps; track step.text; let i = $index; let last = $last) {
              <li class="pipeline__step">
                <span class="pipeline__marker">
                  <ng-icon [name]="step.icon" size="15" />
                </span>
                @if (!last) {
                  <span class="pipeline__line" aria-hidden="true"></span>
                }
                <span class="pipeline__text">{{ step.text }}</span>
              </li>
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
            @for (document of documents(); track document.id; let i = $index) {
              <li class="document-index__row" [style.animation-delay.ms]="i * 40">
                <a [routerLink]="['/cvs', document.id]" class="document-index__link">
                  <span class="document-index__icon">
                    <ng-icon name="lucideFileText" size="16" />
                  </span>
                  <span class="document-index__text">
                    <span class="document-index__name">{{ document.original_filename }}</span>
                    <span class="document-index__meta text-tertiary font-mono">{{
                      document.created_at | date: 'mediumDate'
                    }}</span>
                  </span>
                </a>
                <span class="document-index__row-end">
                  <app-status-badge [status]="document.status" />
                  <button
                    type="button"
                    class="document-index__delete"
                    title="Delete"
                    [disabled]="deletingIds().has(document.id)"
                    (click)="deleteDocument(document.id)"
                  >
                    <ng-icon name="lucideTrash2" size="15" />
                  </button>
                </span>
              </li>
            }
          </ul>
          @if (deleteError()) {
            <p class="cv-workspace__delete-error">{{ deleteError() }}</p>
          }
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
        padding: var(--space-5);
        background: var(--surface-raised);
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-lg);
        box-shadow: var(--shadow-document);
        position: sticky;
        top: var(--space-6);
      }
      .cv-workspace__uploading {
        color: var(--accent);
        font-size: var(--text-sm);
      }
      .cv-workspace__pipeline {
        margin-top: var(--space-4);
      }

      .pipeline {
        list-style: none;
        margin: 0;
        padding: 0;
      }
      .pipeline__step {
        position: relative;
        display: flex;
        align-items: flex-start;
        gap: var(--space-3);
        padding-bottom: var(--space-5);
      }
      .pipeline__step:last-child {
        padding-bottom: 0;
      }
      .pipeline__marker {
        flex-shrink: 0;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 32px;
        height: 32px;
        border-radius: var(--radius-pill);
        background: var(--accent-tint);
        color: var(--accent-strong);
        border: 1px solid var(--border-subtle);
        z-index: 1;
      }
      .pipeline__line {
        position: absolute;
        top: 32px;
        left: 15px;
        bottom: 0;
        width: 1.5px;
        background: var(--border-subtle);
      }
      .pipeline__text {
        padding-top: 6px;
        color: var(--ink-secondary);
        font-size: var(--text-sm);
      }

      .cv-workspace__list {
        display: flex;
        flex-direction: column;
        gap: var(--space-4);
        padding: var(--space-5);
        background: var(--surface-raised);
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-lg);
        box-shadow: var(--shadow-document);
        max-height: calc(100vh - 160px);
      }
      .cv-workspace__list h2 {
        flex-shrink: 0;
      }
      .document-index {
        list-style: none;
        margin: 0;
        padding: 0;
        border-top: 1px solid var(--border-subtle);
        overflow-y: auto;
        overflow-x: hidden;
        min-height: 0;
      }
      .document-index__row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: var(--space-3);
        padding: var(--space-3) var(--space-2);
        margin: 0 calc(var(--space-2) * -1);
        border-bottom: 1px solid var(--border-subtle);
        border-radius: var(--radius-sm);
        animation: document-row-in var(--motion-slow) var(--motion-ease) both;
        transition: background var(--motion-fast) var(--motion-ease);
      }
      .document-index__row:hover {
        background: var(--surface-sunken);
      }
      .document-index__link {
        display: flex;
        align-items: center;
        gap: var(--space-3);
        text-decoration: none;
        min-width: 0;
      }
      .document-index__icon {
        flex-shrink: 0;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 32px;
        height: 32px;
        border-radius: var(--radius-sm);
        background: var(--accent-tint);
        color: var(--accent-strong);
        transition: transform var(--motion-base) var(--motion-spring);
      }
      .document-index__row:hover .document-index__icon {
        transform: scale(1.08);
      }
      .document-index__text {
        display: flex;
        flex-direction: column;
        gap: 2px;
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
      .document-index__row-end {
        display: flex;
        align-items: center;
        gap: var(--space-3);
        flex-shrink: 0;
      }
      .document-index__delete {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 28px;
        height: 28px;
        border: none;
        background: none;
        color: var(--ink-tertiary);
        border-radius: var(--radius-sm);
        cursor: pointer;
        transition: background var(--motion-fast) var(--motion-ease), color var(--motion-fast) var(--motion-ease);
      }
      .document-index__delete:hover:not(:disabled) {
        background: var(--negative-tint);
        color: var(--negative);
      }
      .document-index__delete:disabled {
        opacity: 0.4;
        cursor: default;
      }
      .cv-workspace__delete-error {
        margin: var(--space-2) 0 0;
        padding: var(--space-2) var(--space-3);
        background: var(--negative-tint);
        color: var(--negative);
        border-radius: var(--radius-sm);
        font-size: var(--text-sm);
      }

      @keyframes document-row-in {
        from {
          opacity: 0;
          transform: translateX(8px);
        }
        to {
          opacity: 1;
          transform: translateX(0);
        }
      }

      @media (prefers-reduced-motion: reduce) {
        .document-index__row {
          animation: none;
        }
        .document-index__icon {
          transition: none;
        }
      }

      @media (max-width: 900px) {
        .cv-workspace {
          grid-template-columns: minmax(0, 1fr);
        }
        .cv-workspace__upload {
          position: static;
        }
        .cv-workspace__list {
          max-height: 480px;
        }
      }
    `,
  ],
})
export class CvListComponent implements OnInit {
  protected readonly pipelineSteps = PIPELINE_STEPS;
  protected readonly documents = signal<DocumentSummary[]>([]);
  protected readonly uploading = signal(false);
  protected readonly deletingIds = signal<ReadonlySet<string>>(new Set());
  protected readonly deleteError = signal<string | null>(null);

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

  deleteDocument(documentId: string): void {
    if (this.deletingIds().has(documentId)) return;
    const confirmed = window.confirm(
      'Delete this CV? This also removes any analysis, recommendations, and tailored versions built from it.',
    );
    if (!confirmed) return;

    this.deleteError.set(null);
    this.deletingIds.update((ids) => new Set(ids).add(documentId));
    this.cvApi.delete(documentId).subscribe({
      next: () => {
        this.documents.update((docs) => docs.filter((document) => document.id !== documentId));
        this.clearDeleting(documentId);
      },
      error: () => {
        this.deleteError.set('Could not delete this CV. Please try again.');
        this.clearDeleting(documentId);
      },
    });
  }

  private clearDeleting(documentId: string): void {
    this.deletingIds.update((ids) => {
      const next = new Set(ids);
      next.delete(documentId);
      return next;
    });
  }

  private refresh(): void {
    this.cvApi.list().subscribe((documents) => this.documents.set(documents));
  }
}
