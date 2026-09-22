import { ChangeDetectionStrategy, Component, Input } from '@angular/core';
import { Evidence } from '../../../models/evidence.model';

const SECTION_LABELS: Record<string, string> = {
  SUMMARY: 'Summary',
  EXPERIENCE: 'Experience',
  EDUCATION: 'Education',
  SKILLS: 'Skills',
  PROJECTS: 'Projects',
  CERTIFICATIONS: 'Certifications',
  LANGUAGES: 'Languages',
  REQUIREMENTS: 'Requirements',
  RESPONSIBILITIES: 'Responsibilities',
  OTHER: 'Document',
};

/**
 * Reusable "where did this come from" presentation (section 45):
 *
 *   Technical Skills - Page 2
 *   "Python, Django, PostgreSQL..."
 *
 * Never renders a raw database id - Evidence itself never carries one
 * (see backend interfaces/api/v1/cvs/serializers.py::EvidenceSerializer).
 */
@Component({
  selector: 'app-evidence-note',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <figure class="evidence-note">
      <figcaption class="evidence-note__source">
        {{ sourceLabel }}
      </figcaption>
      <blockquote class="evidence-note__quote">{{ evidence.text }}</blockquote>
    </figure>
  `,
  styles: [
    `
      .evidence-note {
        margin: 0;
        padding-left: var(--space-3);
        border-left: 2px solid var(--border-subtle);
      }
      .evidence-note__source {
        font-family: var(--font-mono);
        font-size: var(--text-xs);
        color: var(--ink-tertiary);
        margin-bottom: 2px;
      }
      .evidence-note__quote {
        margin: 0;
        font-size: var(--text-sm);
        color: var(--ink-secondary);
        font-style: italic;
      }
    `,
  ],
})
export class EvidenceNoteComponent {
  @Input({ required: true }) evidence!: Evidence;

  get sourceLabel(): string {
    const section = this.evidence.section ? SECTION_LABELS[this.evidence.section] ?? this.evidence.section : 'Document';
    const page = this.evidence.page_number ? `Page ${this.evidence.page_number}` : null;
    return page ? `${section} - ${page}` : section;
  }
}
