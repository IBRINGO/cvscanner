import { ChangeDetectionStrategy, Component, EventEmitter, Input, Output, signal } from '@angular/core';

/**
 * Generic drag-and-drop file upload surface (section 42). Deliberately
 * not a `<input type="file">` wrapped in a card - the dropzone IS the
 * primary visual element, communicating format/size constraints
 * directly rather than relying on browser-default file picker chrome.
 */
@Component({
  selector: 'app-upload-dropzone',
  standalone: true,
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
        border: 1px dashed var(--border-strong);
        border-radius: var(--radius-md);
        padding: var(--space-7) var(--space-5);
        text-align: center;
        background: var(--surface-raised);
      }
      .dropzone[data-dragover='true'] {
        border-color: var(--accent);
        background: var(--accent-tint);
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
        gap: var(--space-2);
        pointer-events: none;
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
