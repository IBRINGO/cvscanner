import { NgTemplateOutlet } from '@angular/common';
import { ChangeDetectionStrategy, Component, EventEmitter, Input, Output } from '@angular/core';
import { CandidateProfile } from '../../../cvs/models/candidate-profile.model';
import {
  CvSectionRef,
  SECTION_LABELS,
  SIDEBAR_SECTION_KINDS,
} from '../../../cvs/models/cv-document.model';
import { formatEnumLabel } from '../../../../shared/utils/format-label';
import { TemplateDefinition } from '../../models/template-definition.model';

/** The masthead (name/contact) isn't a reorderable CvSectionRef - it's
 * always present - so it gets its own sentinel id for interactive
 * click-to-select, distinct from any real section id. */
export const PERSONAL_INFO_ID = 'personal-info';

/**
 * The one data-driven CV renderer behind every template (section: "Do
 * not duplicate the CV data for every template"). The same
 * CandidateProfile + section order/visibility renders through six
 * distinct visual treatments purely via [data-template]/[data-columns]
 * CSS - no per-template component, no per-template data copy. All
 * output is plain text in HTML: no text-in-images, nothing that would
 * break ATS parsing.
 */
@Component({
  selector: 'app-cv-document-renderer',
  standalone: true,
  imports: [NgTemplateOutlet],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <article class="cv-page" [attr.data-template]="template.id" [attr.data-columns]="template.columns">
      <header
        class="cv-page__header cv-section-slot"
        [attr.data-interactive]="interactive"
        [attr.data-selected]="interactive && selectedSectionId === PERSONAL_INFO_ID"
        (click)="onSectionClick(PERSONAL_INFO_ID)"
      >
        <h1 class="cv-page__name">{{ profile.full_name ?? 'Unnamed candidate' }}</h1>
        @if (contactLine()) {
          <p class="cv-page__contact">{{ contactLine() }}</p>
        }
      </header>

      @if (template.columns === 2) {
        <div class="cv-page__body cv-page__body--split">
          <aside class="cv-page__sidebar">
            @for (ref of sidebarSections(); track ref.id) {
              <div
                class="cv-section-slot"
                [attr.data-interactive]="interactive"
                [attr.data-selected]="interactive && ref.id === selectedSectionId"
                (click)="onSectionClick(ref.id)"
              >
                <ng-container *ngTemplateOutlet="section; context: { $implicit: ref }" />
              </div>
            }
          </aside>
          <div class="cv-page__main">
            @for (ref of mainSections(); track ref.id) {
              <div
                class="cv-section-slot"
                [attr.data-interactive]="interactive"
                [attr.data-selected]="interactive && ref.id === selectedSectionId"
                (click)="onSectionClick(ref.id)"
              >
                <ng-container *ngTemplateOutlet="section; context: { $implicit: ref }" />
              </div>
            }
          </div>
        </div>
      } @else {
        <div class="cv-page__body">
          @for (ref of visibleSections(); track ref.id) {
            <div
              class="cv-section-slot"
              [attr.data-interactive]="interactive"
              [attr.data-selected]="interactive && ref.id === selectedSectionId"
              (click)="onSectionClick(ref.id)"
            >
              <ng-container *ngTemplateOutlet="section; context: { $implicit: ref }" />
            </div>
          }
        </div>
      }
    </article>

    <ng-template #section let-ref>
      @switch (ref.kind) {
        @case ('summary') {
          @if (profile.summary) {
            <section class="cv-section">
              <h2>Summary</h2>
              <p>{{ profile.summary }}</p>
            </section>
          }
        }
        @case ('experience') {
          @if (profile.experiences.length > 0) {
            <section class="cv-section">
              <h2>Experience</h2>
              @for (exp of profile.experiences; track $index) {
                <div class="cv-entry">
                  <div class="cv-entry__head">
                    <span class="cv-entry__title"
                      >{{ exp.title ?? 'Role' }}@if (exp.company) {, {{ exp.company }}}</span
                    >
                    @if (exp.start_date_raw) {
                      <span class="cv-entry__dates">{{ exp.start_date_raw }} - {{ exp.end_date_raw ?? 'Present' }}</span>
                    }
                  </div>
                  @if (exp.description) {
                    <p class="cv-entry__desc">{{ exp.description }}</p>
                  }
                  @if (exp.achievements.length > 0) {
                    <ul class="cv-entry__list">
                      @for (item of exp.achievements; track $index) {
                        <li>{{ item }}</li>
                      }
                    </ul>
                  }
                </div>
              }
            </section>
          }
        }
        @case ('education') {
          @if (profile.education.length > 0) {
            <section class="cv-section">
              <h2>Education</h2>
              @for (entry of profile.education; track $index) {
                <div class="cv-entry">
                  <div class="cv-entry__head">
                    <span class="cv-entry__title"
                      >{{ entry.degree ?? 'Program' }}@if (entry.institution) {, {{ entry.institution }}}</span
                    >
                    @if (entry.start_date_raw) {
                      <span class="cv-entry__dates">{{ entry.start_date_raw }} - {{ entry.end_date_raw ?? '' }}</span>
                    }
                  </div>
                </div>
              }
            </section>
          }
        }
        @case ('skills') {
          @if (profile.skills.length > 0) {
            <section class="cv-section">
              <h2>Skills</h2>
              <p class="cv-page__skill-line">
                @for (skill of profile.skills; track $index; let last = $last) {
                  {{ skill.skill?.canonical_name ?? skill.raw_text }}@if (!last) {, }
                }
              </p>
            </section>
          }
        }
        @case ('projects') {
          @if (profile.projects.length > 0) {
            <section class="cv-section">
              <h2>Projects</h2>
              @for (project of profile.projects; track project.name) {
                <div class="cv-entry">
                  <span class="cv-entry__title">{{ project.name }}</span>
                  @if (project.description) {
                    <p class="cv-entry__desc">{{ project.description }}</p>
                  }
                </div>
              }
            </section>
          }
        }
        @case ('certifications') {
          @if (profile.certifications.length > 0) {
            <section class="cv-section">
              <h2>Certifications</h2>
              @for (cert of profile.certifications; track cert.name) {
                <div class="cv-entry cv-entry--tight">
                  <span class="cv-entry__title"
                    >{{ cert.name }}@if (cert.issuer) {, {{ cert.issuer }}}</span
                  >
                </div>
              }
            </section>
          }
        }
        @case ('languages') {
          @if (profile.languages.length > 0) {
            <section class="cv-section">
              <h2>Languages</h2>
              <p class="cv-page__skill-line">
                @for (lang of profile.languages; track lang.name; let last = $last) {
                  {{ lang.canonical_name ?? lang.name }}
                  @if (lang.proficiency_normalized && lang.proficiency_normalized !== 'UNKNOWN') {
                    ({{ formatEnumLabel(lang.proficiency_normalized) }})
                  }
                  @if (!last) {, }
                }
              </p>
            </section>
          }
        }
        @case ('custom') {
          <section class="cv-section">
            <h2>{{ ref.title }}</h2>
            <p class="cv-entry__desc">{{ ref.content }}</p>
          </section>
        }
      }
    </ng-template>
  `,
  styleUrl: './cv-document-renderer.component.scss',
})
export class CvDocumentRendererComponent {
  protected readonly PERSONAL_INFO_ID = PERSONAL_INFO_ID;

  @Input({ required: true }) profile!: CandidateProfile;
  @Input({ required: true }) sectionOrder!: CvSectionRef[];
  @Input() hiddenSectionIds: string[] = [];
  @Input({ required: true }) template!: TemplateDefinition;
  /** When true, sections are clickable and the selected one is
   * highlighted - used by the CV editor so a candidate can select a
   * section directly on the rendered document, not only from a side
   * list. Read-only contexts (template gallery, tailoring preview)
   * leave this false so nothing there looks clickable. */
  @Input() interactive = false;
  @Input() selectedSectionId: string | null = null;
  @Output() sectionSelected = new EventEmitter<string>();

  protected readonly SECTION_LABELS = SECTION_LABELS;

  onSectionClick(id: string): void {
    if (this.interactive) this.sectionSelected.emit(id);
  }

  formatEnumLabel(value: string | null | undefined): string {
    return formatEnumLabel(value);
  }

  visibleSections(): CvSectionRef[] {
    return this.sectionOrder.filter((ref) => !this.hiddenSectionIds.includes(ref.id));
  }

  sidebarSections(): CvSectionRef[] {
    return this.visibleSections().filter((ref) => SIDEBAR_SECTION_KINDS.has(ref.kind));
  }

  mainSections(): CvSectionRef[] {
    return this.visibleSections().filter((ref) => !SIDEBAR_SECTION_KINDS.has(ref.kind));
  }

  contactLine(): string {
    const items = [this.profile.email, this.profile.phone, this.profile.location, ...this.profile.links].filter(
      (item): item is string => !!item,
    );
    return items.join('  |  ');
  }
}
