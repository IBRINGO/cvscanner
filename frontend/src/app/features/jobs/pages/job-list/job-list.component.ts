import { DatePipe } from '@angular/common';
import { ChangeDetectionStrategy, Component, OnInit, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { NgIcon, provideIcons } from '@ng-icons/core';
import { CVSCANNER_ICONS } from '../../../../core/icons';
import { StatusBadgeComponent } from '../../../../shared/components/ui/status-badge/status-badge.component';
import { UploadDropzoneComponent } from '../../../../shared/components/ui/upload-dropzone/upload-dropzone.component';
import { DocumentSummary } from '../../../../shared/models/document.model';
import { JobApiService } from '../../services/job-api.service';

type InputMode = 'text' | 'file';

@Component({
  selector: 'app-job-list-page',
  standalone: true,
  imports: [UploadDropzoneComponent, StatusBadgeComponent, RouterLink, DatePipe, FormsModule, NgIcon],
  viewProviders: [provideIcons(CVSCANNER_ICONS)],
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
            <ng-icon name="lucideFileText" size="15" />
            Paste text
          </button>
          <button
            type="button"
            role="tab"
            [attr.aria-selected]="mode() === 'file'"
            [attr.data-active]="mode() === 'file'"
            (click)="mode.set('file')"
          >
            <ng-icon name="lucideFileUp" size="15" />
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
            <ng-icon name="lucideSparkles" size="15" />
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
            @for (document of documents(); track document.id; let i = $index) {
              <li class="document-index__row" [style.animation-delay.ms]="i * 40">
                <a [routerLink]="['/jobs', document.id]" class="document-index__link">
                  <span class="document-index__icon">
                    <ng-icon name="lucideBriefcase" size="16" />
                  </span>
                  <span class="document-index__text">
                    <span class="document-index__name">{{ document.original_filename }}</span>
                    <span class="document-index__meta text-tertiary font-mono">{{
                      document.created_at | date: 'mediumDate'
                    }}</span>
                  </span>
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
        padding: var(--space-5);
        background: var(--surface-raised);
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-lg);
        box-shadow: var(--shadow-document);
        position: sticky;
        top: var(--space-6);
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
        display: inline-flex;
        align-items: center;
        gap: var(--space-2);
        border: none;
        background: transparent;
        padding: var(--space-2) var(--space-4);
        border-radius: var(--radius-pill);
        font-size: var(--text-sm);
        cursor: pointer;
        color: var(--ink-secondary);
        transition:
          background var(--motion-fast) var(--motion-ease),
          color var(--motion-fast) var(--motion-ease);
      }
      .job-workspace__toggle button[data-active='true'] {
        background: var(--surface-raised);
        color: var(--accent-strong);
        font-weight: 600;
        box-shadow: var(--shadow-document);
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
        transition: border-color var(--motion-fast) var(--motion-ease);
      }
      .job-workspace__field textarea:focus-visible {
        outline: 2px solid var(--accent);
        outline-offset: 1px;
      }
      .job-workspace__submit {
        display: inline-flex;
        align-items: center;
        gap: var(--space-2);
        align-self: flex-start;
        border: none;
        background: var(--accent);
        color: white;
        padding: var(--space-3) var(--space-5);
        border-radius: var(--radius-sm);
        font-size: var(--text-sm);
        font-weight: 500;
        cursor: pointer;
        transition:
          background var(--motion-fast) var(--motion-ease),
          transform var(--motion-fast) var(--motion-ease);
      }
      .job-workspace__submit:not(:disabled):hover {
        background: var(--accent-strong);
        transform: translateY(-1px);
      }
      .job-workspace__submit:disabled {
        background: var(--border-strong);
        cursor: not-allowed;
      }
      .job-workspace__submitting {
        color: var(--accent);
        font-size: var(--text-sm);
      }

      .job-workspace__list {
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
      .job-workspace__list h2 {
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
        background: var(--surface-sunken);
        color: var(--ink-secondary);
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
        .document-index__icon,
        .job-workspace__submit {
          transition: none;
        }
      }

      @media (max-width: 900px) {
        .job-workspace {
          grid-template-columns: minmax(0, 1fr);
        }
        .job-workspace__upload {
          position: static;
        }
        .job-workspace__list {
          max-height: 480px;
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
