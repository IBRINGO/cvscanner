import { DatePipe } from '@angular/common';
import { ChangeDetectionStrategy, Component, OnInit, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { StatusBadgeComponent } from '../../../../shared/components/ui/status-badge/status-badge.component';
import { UploadDropzoneComponent } from '../../../../shared/components/ui/upload-dropzone/upload-dropzone.component';
import { DocumentSummary } from '../../../../shared/models/document.model';
import { JobApiService } from '../../services/job-api.service';

type InputMode = 'text' | 'file';

@Component({
  selector: 'app-job-list-page',
  standalone: true,
  imports: [UploadDropzoneComponent, StatusBadgeComponent, RouterLink, DatePipe, FormsModule],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <section class="job-workspace">
      <div class="job-workspace__upload">
        <h1>Add a job offer</h1>
        <p class="text-secondary">
          Paste the job description or upload the original file. CVScanner structures it into
          requirements you can compare a profile against later.
        </p>

        <div class="job-workspace__toggle" role="tablist" aria-label="Job offer input method">
          <button
            type="button"
            role="tab"
            [attr.aria-selected]="mode() === 'text'"
            [attr.data-active]="mode() === 'text'"
            (click)="mode.set('text')"
          >
            Paste text
          </button>
          <button
            type="button"
            role="tab"
            [attr.aria-selected]="mode() === 'file'"
            [attr.data-active]="mode() === 'file'"
            (click)="mode.set('file')"
          >
            Upload file
          </button>
        </div>

        @if (mode() === 'text') {
          <label class="job-workspace__field">
            <span class="text-secondary">Job description</span>
            <textarea
              [(ngModel)]="jobText"
              rows="10"
              placeholder="Paste the full job posting here"
            ></textarea>
          </label>
          <button
            type="button"
            class="job-workspace__submit"
            [disabled]="!jobText.trim() || submitting()"
            (click)="submitText()"
          >
            Structure this offer
          </button>
        } @else {
          <app-upload-dropzone
            title="Drop the job offer here"
            hint="PDF or DOCX, up to 10 MB"
            accept=".pdf,.docx"
            inputId="job-upload-input"
            (fileSelected)="onFileSelected($event)"
          />
        }

        @if (submitting()) {
          <p class="job-workspace__submitting" role="status">Submitting...</p>
        }
      </div>

      <div class="job-workspace__list">
        <h2>Your job offers</h2>
        @if (documents().length === 0) {
          <p class="text-secondary">Nothing added yet. Your job offers will appear here.</p>
        } @else {
          <ul class="document-index">
            @for (document of documents(); track document.id) {
              <li class="document-index__row">
                <a [routerLink]="['/jobs', document.id]" class="document-index__link">
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
      .job-workspace {
        display: grid;
        grid-template-columns: minmax(0, 1.1fr) minmax(0, 0.9fr);
        gap: var(--space-7);
        align-items: start;
      }
      .job-workspace__upload {
        display: flex;
        flex-direction: column;
        gap: var(--space-4);
      }
      .job-workspace__toggle {
        display: inline-flex;
        gap: var(--space-1);
        background: var(--surface-sunken);
        padding: 2px;
        border-radius: var(--radius-pill);
        width: fit-content;
      }
      .job-workspace__toggle button {
        border: none;
        background: transparent;
        padding: var(--space-2) var(--space-4);
        border-radius: var(--radius-pill);
        font-size: var(--text-sm);
        cursor: pointer;
        color: var(--ink-secondary);
      }
      .job-workspace__toggle button[data-active='true'] {
        background: var(--surface-raised);
        color: var(--ink-primary);
        font-weight: 500;
      }
      .job-workspace__field {
        display: flex;
        flex-direction: column;
        gap: var(--space-2);
      }
      .job-workspace__field textarea {
        font-family: var(--font-mono);
        font-size: var(--text-sm);
        padding: var(--space-3);
        border: 1px solid var(--border-strong);
        border-radius: var(--radius-sm);
        background: var(--surface-raised);
        color: var(--ink-primary);
        resize: vertical;
      }
      .job-workspace__field textarea:focus-visible {
        outline: 2px solid var(--accent);
        outline-offset: 1px;
      }
      .job-workspace__submit {
        align-self: flex-start;
        border: none;
        background: var(--accent);
        color: white;
        padding: var(--space-3) var(--space-5);
        border-radius: var(--radius-sm);
        font-size: var(--text-sm);
        font-weight: 500;
        cursor: pointer;
      }
      .job-workspace__submit:disabled {
        background: var(--border-strong);
        cursor: not-allowed;
      }
      .job-workspace__submitting {
        color: var(--accent);
        font-size: var(--text-sm);
      }
      .job-workspace__list h2 {
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
        .job-workspace {
          grid-template-columns: minmax(0, 1fr);
        }
      }
    `,
  ],
})
export class JobListComponent implements OnInit {
  protected readonly mode = signal<InputMode>('text');
  protected readonly documents = signal<DocumentSummary[]>([]);
  protected readonly submitting = signal(false);
  protected jobText = '';

  constructor(
    private readonly jobApi: JobApiService,
    private readonly router: Router,
  ) {}

  ngOnInit(): void {
    this.refresh();
  }

  submitText(): void {
    this.submitting.set(true);
    this.jobApi.uploadText(this.jobText).subscribe({
      next: (document) => {
        this.submitting.set(false);
        this.router.navigate(['/jobs', document.id]);
      },
      error: () => this.submitting.set(false),
    });
  }

  onFileSelected(file: File): void {
    this.submitting.set(true);
    this.jobApi.uploadFile(file).subscribe({
      next: (document) => {
        this.submitting.set(false);
        this.router.navigate(['/jobs', document.id]);
      },
      error: () => this.submitting.set(false),
    });
  }

  private refresh(): void {
    this.jobApi.list().subscribe((documents) => this.documents.set(documents));
  }
}
