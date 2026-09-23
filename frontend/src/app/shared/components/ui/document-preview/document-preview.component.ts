import { ChangeDetectionStrategy, Component, Input } from '@angular/core';
import { NgIcon, provideIcons } from '@ng-icons/core';
import { CVSCANNER_ICONS } from '../../../../core/icons';
import { ProcessingStatus } from '../../../models/document.model';
import { StatusBadgeComponent } from '../status-badge/status-badge.component';

/**
 * A realistic paper-like preview of a CV or job document, used wherever
 * the product previously showed a bare file icon. The heading/subheading
 * shown are always real extracted data passed in by the caller (or a
 * neutral "Processing..." placeholder before extraction completes) -
 * the horizontal text bars are a generic "this page has text on it"
 * convention (the same idea as a skeleton loader), never invented
 * document content.
 */
@Component({
  selector: 'app-document-preview',
  standalone: true,
  imports: [NgIcon, StatusBadgeComponent],
  viewProviders: [provideIcons(CVSCANNER_ICONS)],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <figure class="doc" [attr.data-kind]="kind">
      <div class="doc__page">
        @if (status) {
          <div class="doc__status">
            <app-status-badge [status]="status" />
          </div>
        }
        <div class="doc__kind-icon">
          <ng-icon [name]="kind === 'cv' ? 'lucideFileText' : 'lucideBriefcase'" size="14" />
        </div>
        <div class="doc__heading">{{ heading || 'Processing document...' }}</div>
        @if (subheading) {
          <div class="doc__subheading">{{ subheading }}</div>
        }
        <div class="doc__lines">
          <span class="doc__line" style="width: 92%"></span>
          <span class="doc__line" style="width: 78%"></span>
          <span class="doc__line" style="width: 85%"></span>
          <span class="doc__line doc__line--gap" style="width: 60%"></span>
          <span class="doc__line" style="width: 90%"></span>
          <span class="doc__line" style="width: 70%"></span>
        </div>
      </div>
      <figcaption class="doc__caption">
        <span class="doc__filename font-mono">{{ filename }}</span>
        @if (pageLabel) {
          <span class="doc__page-label">{{ pageLabel }}</span>
        }
      </figcaption>
    </figure>
  `,
  styles: [
    `
      .doc {
        margin: 0;
        display: flex;
        flex-direction: column;
        gap: var(--space-2);
        width: 100%;
        max-width: 220px;
      }
      .doc__page {
        background: var(--paper-surface);
        border: 1px solid var(--paper-border);
        border-radius: var(--radius-sm);
        box-shadow: var(--shadow-document);
        color: var(--paper-ink);
        position: relative;
        aspect-ratio: 3 / 4;
        padding: var(--space-4) var(--space-3);
        display: flex;
        flex-direction: column;
        gap: var(--space-2);
      }
      .doc__status {
        position: absolute;
        top: var(--space-2);
        right: var(--space-2);
      }
      .doc__kind-icon {
        color: var(--paper-ink-secondary);
        opacity: 0.7;
      }
      .doc__heading {
        font-family: var(--font-display);
        font-weight: 600;
        font-size: var(--text-sm);
        color: var(--paper-ink);
        line-height: 1.25;
        overflow: hidden;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
      }
      .doc__subheading {
        font-size: var(--text-xs);
        color: var(--paper-ink-secondary);
        margin-top: calc(var(--space-1) * -1);
      }
      .doc__lines {
        display: flex;
        flex-direction: column;
        gap: 6px;
        margin-top: var(--space-2);
      }
      .doc__line {
        display: block;
        height: 5px;
        border-radius: 2px;
        background: var(--paper-border);
        opacity: 0.8;
      }
      .doc__line--gap {
        margin-top: 6px;
      }
      .doc__caption {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: var(--space-2);
        font-size: var(--text-xs);
        color: var(--ink-tertiary);
      }
      .doc__filename {
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }
      .doc__page-label {
        flex-shrink: 0;
      }
    `,
  ],
})
export class DocumentPreviewComponent {
  @Input({ required: true }) kind!: 'cv' | 'job';
  @Input() heading = '';
  @Input() subheading = '';
  @Input() filename = '';
  @Input() status?: ProcessingStatus;
  @Input() pageLabel = '';
}
