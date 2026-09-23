import { ChangeDetectionStrategy, Component, OnInit, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { NgIcon, provideIcons } from '@ng-icons/core';
import { CVSCANNER_ICONS } from '../../../../core/icons';
import { CvDocumentRendererComponent } from '../../components/cv-document-renderer/cv-document-renderer.component';
import { CandidateProfile } from '../../../cvs/models/candidate-profile.model';
import { DEFAULT_SECTION_ORDER } from '../../../cvs/models/cv-document.model';
import { CvApiService } from '../../../cvs/services/cv-api.service';
import { CV_TEMPLATES } from '../../models/template-definition.model';
import { SAMPLE_PROFILE } from '../../models/sample-profile';

/**
 * The reference width the renderer is measured at before being scaled
 * down into a thumbnail - must match `.cv-page`'s `max-width` in
 * cv-document-renderer.component.scss so the thumbnail is a faithful
 * miniature of the real page, not a different layout.
 */
const THUMB_REFERENCE_WIDTH = 760;
const THUMB_WIDTH = 280;
const THUMB_SCALE = THUMB_WIDTH / THUMB_REFERENCE_WIDTH;
/** A4 (210 x 297mm) - real CVs are printed on A4, so the thumbnail crop
 * should read as an actual sheet of paper, not an arbitrary rectangle. */
const A4_RATIO = '210 / 297';

/**
 * The template gallery: full-size, realistic previews so templates can
 * actually be compared, not a grid of generic file icons. Each card
 * renders the same live CvDocumentRenderer used by the editor/export,
 * scaled down into a crisp paper thumbnail - never a separately
 * generated (and therefore driftable) preview image. Previews use the
 * visitor's own most recently processed CV when one exists (their real
 * data through every template); otherwise a clearly-labelled sample
 * profile, never a fabricated "real" candidate.
 */
@Component({
  selector: 'app-template-gallery-page',
  standalone: true,
  imports: [RouterLink, CvDocumentRendererComponent, NgIcon],
  viewProviders: [provideIcons(CVSCANNER_ICONS)],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <header class="gallery__header">
      <h1>Templates</h1>
      <p class="text-secondary">
        Six ATS-friendly templates, rendered live from the same profile.
        @if (usingSample()) {
          These previews use sample data -
          <a routerLink="/cvs">upload a CV</a>
          to preview with your own.
        } @else if (profile()?.full_name) {
          Previewing with {{ profile()?.full_name }}'s CV.
        } @else {
          Previewing with your most recent CV.
        }
      </p>
    </header>

    <div class="gallery__grid">
      @for (t of templates; track t.id; let i = $index) {
        <article class="gallery__card" [style.animation-delay.ms]="i * 60">
          <a
            class="gallery__thumb-link"
            [routerLink]="cvId() ? ['/cvs', cvId(), 'editor'] : ['/cvs']"
            [queryParams]="cvId() ? { template: t.id } : null"
            [attr.aria-label]="'Preview and use the ' + t.name + ' template'"
          >
            <div class="gallery__thumb">
              @if (profile(); as p) {
                <div class="gallery__thumb-canvas">
                  <app-cv-document-renderer [profile]="p" [sectionOrder]="sectionOrder" [template]="t" />
                </div>
              }
              <div class="gallery__thumb-fade"></div>
              <div class="gallery__thumb-overlay">
                <ng-icon name="lucideEye" size="16" />
                {{ cvId() ? 'Preview with your CV' : 'Preview template' }}
              </div>
            </div>
          </a>
          <div class="gallery__meta">
            <div class="gallery__badges">
              <span class="gallery__badge">{{ t.columns }}-column</span>
              <span class="gallery__badge gallery__badge--ats">
                <ng-icon name="lucideCircleCheck" size="12" />
                ATS-friendly
              </span>
            </div>
            <h2>{{ t.name }}</h2>
            <p class="text-secondary">{{ t.description }}</p>
            @if (cvId(); as id) {
              <a [routerLink]="['/cvs', id, 'editor']" [queryParams]="{ template: t.id }" class="gallery__select">
                Select this template
                <ng-icon name="lucideArrowUpRight" size="14" />
              </a>
            } @else {
              <a routerLink="/cvs" class="gallery__select gallery__select--secondary">Upload a CV to use this template</a>
            }
          </div>
        </article>
      }
    </div>
  `,
  styles: [
    `
      .gallery__header {
        display: flex;
        flex-direction: column;
        gap: var(--space-2);
        margin-bottom: var(--space-6);
        max-width: 720px;
      }
      .gallery__grid {
        display: grid;
        grid-template-columns: repeat(3, ${THUMB_WIDTH}px);
        justify-content: center;
        gap: var(--space-8) var(--space-7);
      }
      @media (max-width: 1120px) {
        .gallery__grid {
          grid-template-columns: repeat(2, ${THUMB_WIDTH}px);
        }
      }
      @media (max-width: 720px) {
        .gallery__grid {
          grid-template-columns: repeat(1, ${THUMB_WIDTH}px);
        }
      }
      .gallery__card {
        display: flex;
        flex-direction: column;
        gap: var(--space-3);
        width: ${THUMB_WIDTH}px;
        animation: gallery-card-in var(--motion-slow) var(--motion-ease) both;
      }
      .gallery__thumb-link {
        display: block;
        text-decoration: none;
        border-radius: var(--radius-md);
        outline-offset: 3px;
      }
      .gallery__thumb {
        position: relative;
        width: ${THUMB_WIDTH}px;
        aspect-ratio: ${A4_RATIO};
        overflow: hidden;
        border-radius: var(--radius-md);
        border: 1px solid var(--paper-border);
        background: var(--paper-surface);
        box-shadow: var(--shadow-document);
        transition:
          transform var(--motion-base) var(--motion-spring),
          box-shadow var(--motion-base) var(--motion-ease),
          border-color var(--motion-base) var(--motion-ease);
      }
      .gallery__thumb-link:hover .gallery__thumb,
      .gallery__thumb-link:focus-visible .gallery__thumb {
        transform: translateY(-6px);
        box-shadow: var(--shadow-overlay);
        border-color: var(--accent);
      }
      .gallery__thumb-canvas {
        position: absolute;
        top: 0;
        left: 0;
        width: ${THUMB_REFERENCE_WIDTH}px;
        transform: scale(${THUMB_SCALE});
        transform-origin: top left;
        pointer-events: none;
      }
      .gallery__thumb-fade {
        position: absolute;
        left: 0;
        right: 0;
        bottom: 0;
        height: 56px;
        background: linear-gradient(to bottom, transparent, var(--paper-surface));
        pointer-events: none;
      }
      .gallery__thumb-overlay {
        position: absolute;
        inset: 0;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: var(--space-2);
        background: rgba(15, 23, 42, 0.55);
        color: #fff;
        font-size: var(--text-sm);
        font-weight: 600;
        text-align: center;
        padding: 0 var(--space-3);
        opacity: 0;
        transform: translateY(4px);
        transition:
          opacity var(--motion-base) var(--motion-ease),
          transform var(--motion-base) var(--motion-ease);
      }
      .gallery__thumb-link:hover .gallery__thumb-overlay,
      .gallery__thumb-link:focus-visible .gallery__thumb-overlay {
        opacity: 1;
        transform: translateY(0);
      }
      .gallery__badges {
        display: flex;
        gap: var(--space-2);
        margin-bottom: var(--space-1);
      }
      .gallery__badge {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        padding: 2px var(--space-2);
        border-radius: var(--radius-pill);
        background: var(--surface-sunken);
        color: var(--ink-secondary);
        font-size: var(--text-xs);
        font-weight: 600;
      }
      .gallery__badge--ats {
        background: var(--positive-tint);
        color: var(--positive);
      }
      .gallery__meta h2 {
        margin-bottom: 2px;
      }
      .gallery__select {
        display: inline-flex;
        align-items: center;
        gap: var(--space-2);
        margin-top: var(--space-2);
        padding: var(--space-2) var(--space-4);
        border-radius: var(--radius-sm);
        background: var(--accent);
        color: #fff;
        font-size: var(--text-sm);
        font-weight: 600;
        text-decoration: none;
        width: fit-content;
        transition:
          background var(--motion-fast) var(--motion-ease),
          transform var(--motion-fast) var(--motion-ease);
      }
      .gallery__select:hover {
        background: var(--accent-strong);
        transform: translateY(-1px);
      }
      .gallery__select--secondary {
        background: none;
        border: 1px solid var(--border-strong);
        color: var(--ink-primary);
      }
      .gallery__select--secondary:hover {
        background: var(--surface-sunken);
        transform: none;
      }

      @keyframes gallery-card-in {
        from {
          opacity: 0;
          transform: translateY(18px);
        }
        to {
          opacity: 1;
          transform: translateY(0);
        }
      }

      @media (prefers-reduced-motion: reduce) {
        .gallery__card {
          animation: none;
        }
        .gallery__thumb,
        .gallery__thumb-overlay,
        .gallery__select {
          transition: none;
        }
      }
    `,
  ],
})
export class TemplateGalleryComponent implements OnInit {
  protected readonly templates = CV_TEMPLATES;
  protected readonly sectionOrder = DEFAULT_SECTION_ORDER;
  protected readonly profile = signal<CandidateProfile | null>(SAMPLE_PROFILE);
  protected readonly usingSample = signal(true);
  protected readonly cvId = signal<string | null>(null);

  constructor(private readonly cvApi: CvApiService) {}

  ngOnInit(): void {
    this.cvApi.list().subscribe((docs) => {
      const processed = docs
        .filter((doc) => doc.status === 'PROCESSED')
        .sort((a, b) => (a.updated_at < b.updated_at ? 1 : -1));
      const mostRecent = processed[0];
      if (!mostRecent) return;

      this.cvApi.getProfile(mostRecent.id).subscribe((response) => {
        if (!response.profile) return;
        this.profile.set(response.profile);
        this.usingSample.set(false);
        this.cvId.set(mostRecent.id);
      });
    });
  }
}
