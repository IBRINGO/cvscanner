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
 * The template gallery: full-size, realistic previews so templates can
 * actually be compared, not a grid of tiny thumbnails. Previews use the
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
        Six ATS-friendly templates, rendered from the same profile.
        @if (usingSample()) {
          These previews use sample data -
          <a routerLink="/cvs">upload a CV</a>
          to preview with your own.
        } @else {
          Previewing with {{ profile()?.full_name }}'s CV.
        }
      </p>
    </header>

    <div class="gallery__grid">
      @for (t of templates; track t.id) {
        <article class="gallery__card">
          <div class="gallery__preview">
            @if (profile(); as p) {
              <app-cv-document-renderer
                [profile]="p"
                [sectionOrder]="sectionOrder"
                [template]="t"
              />
            }
          </div>
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
        grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
        gap: var(--space-6);
      }
      .gallery__card {
        display: flex;
        flex-direction: column;
        gap: var(--space-3);
      }
      .gallery__preview {
        transform: scale(0.62);
        transform-origin: top center;
        height: 340px;
        overflow: hidden;
        border-radius: var(--radius-md);
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
      }
      .gallery__select:hover {
        background: var(--accent-strong);
      }
      .gallery__select--secondary {
        background: none;
        border: 1px solid var(--border-strong);
        color: var(--ink-primary);
      }
      .gallery__select--secondary:hover {
        background: var(--surface-sunken);
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
