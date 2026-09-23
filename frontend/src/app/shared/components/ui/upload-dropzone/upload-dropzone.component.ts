import { ChangeDetectionStrategy, Component, EventEmitter, Input, Output, signal } from '@angular/core';
import { NgIcon, provideIcons } from '@ng-icons/core';
import { CVSCANNER_ICONS } from '../../../../core/icons';

/**
 * Generic drag-and-drop file upload surface (section 42). Deliberately
 * not a `<input type="file">` wrapped in a card - the dropzone IS the
 * primary visual element, communicating format/size constraints
 * directly rather than relying on browser-default file picker chrome.
 */
@Component({
  selector: 'app-upload-dropzone',
  standalone: true,
  imports: [NgIcon],
  viewProviders: [provideIcons(CVSCANNER_ICONS)],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div
      class="dropzone"
      [attr.data-dragover]="dragOver()"
      (dragover)="onDragOver($event)"
      (dragleave)="onDragLeave()"
      (drop)="onDrop($event)"
    >
      <input
        #fileInput
        type="file"
        [accept]="accept"
        class="dropzone__input"
        [id]="inputId"
        (change)="onFileInputChange($event)"
      />
      <label [for]="inputId" class="dropzone__label">
        <span class="dropzone__icon">
          <ng-icon name="lucideFileUp" size="26" />
        </span>
        <span class="dropzone__title">{{ title }}</span>
        <span class="dropzone__hint">{{ hint }}</span>
        <span class="dropzone__cta">Choose a file, or drop it here</span>
      </label>
    </div>
  `,
  styles: [
    `
      .dropzone {
        position: relative;
        border: 1.5px dashed var(--border-strong);
        border-radius: var(--radius-lg);
        padding: var(--space-7) var(--space-5);
        text-align: center;
        background: var(--surface-raised);
        transition:
          border-color var(--motion-base) var(--motion-ease),
          background var(--motion-base) var(--motion-ease),
          box-shadow var(--motion-base) var(--motion-ease);
      }
      .dropzone:hover {
        border-color: var(--accent);
        box-shadow: var(--shadow-document);
      }
      .dropzone[data-dragover='true'] {
        border-color: var(--accent);
        border-style: solid;
        background: var(--accent-tint);
        box-shadow: var(--shadow-overlay);
      }
      .dropzone__input {
        position: absolute;
        inset: 0;
        opacity: 0;
        cursor: pointer;
        width: 100%;
        height: 100%;
      }
      .dropzone__label {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: var(--space-2);
        pointer-events: none;
      }
      .dropzone__icon {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 56px;
        height: 56px;
        margin-bottom: var(--space-2);
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-pill);
        background: var(--accent-tint);
        color: var(--accent-strong);
        transition:
          transform var(--motion-base) var(--motion-spring),
          background var(--motion-base) var(--motion-ease);
      }
      .dropzone:hover .dropzone__icon {
        transform: translateY(-3px) scale(1.05);
      }
      .dropzone[data-dragover='true'] .dropzone__icon {
        background: var(--accent);
        color: #fff;
        transform: scale(1.1);
      }
      .dropzone__title {
        font-family: var(--font-display);
        font-size: var(--text-lg);
        color: var(--ink-primary);
      }
      .dropzone__hint {
        color: var(--ink-secondary);
        font-size: var(--text-sm);
      }
      .dropzone__cta {
        margin-top: var(--space-2);
        font-size: var(--text-sm);
        font-weight: 500;
        color: var(--accent);
      }

      @media (prefers-reduced-motion: reduce) {
        .dropzone,
        .dropzone__icon {
          transition: none;
        }
        .dropzone:hover .dropzone__icon {
          transform: none;
        }
      }
    `,
  ],
})
export class UploadDropzoneComponent {
  @Input({ required: true }) title!: string;
  @Input({ required: true }) hint!: string;
  @Input() accept = '';
  @Input() inputId = 'upload-dropzone-input';
  @Output() fileSelected = new EventEmitter<File>();

  protected readonly dragOver = signal(false);

  onDragOver(event: DragEvent): void {
    event.preventDefault();
    this.dragOver.set(true);
  }

  onDragLeave(): void {
    this.dragOver.set(false);
  }

  onDrop(event: DragEvent): void {
    event.preventDefault();
    this.dragOver.set(false);
    const file = event.dataTransfer?.files?.[0];
    if (file) {
      this.fileSelected.emit(file);
    }
  }

  onFileInputChange(event: Event): void {
    const file = (event.target as HTMLInputElement).files?.[0];
    if (file) {
      this.fileSelected.emit(file);
    }
  }
}
