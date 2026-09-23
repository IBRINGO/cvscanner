import { ChangeDetectionStrategy, Component, OnInit, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
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
  imports: [RouterLink, CvDocumentRendererComponent],
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
            <h2>{{ t.name }}</h2>
            <p class="text-secondary">{{ t.description }}</p>
            @if (cvId(); as id) {
              <a [routerLink]="['/cvs', id, 'editor']" [queryParams]="{ template: t.id }" class="gallery__use">
                Use this template
              </a>
            } @else {
              <a routerLink="/cvs" class="gallery__use">Upload a CV to use this template</a>
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
      .gallery__meta h2 {
        margin-bottom: 2px;
      }
      .gallery__use {
        display: inline-block;
        margin-top: var(--space-2);
        font-size: var(--text-sm);
        font-weight: 600;
        color: var(--accent);
        text-decoration: none;
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
