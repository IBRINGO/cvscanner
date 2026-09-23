export type TemplateColumns = 1 | 2;

export interface TemplateDefinition {
  id: string;
  name: string;
  description: string;
  columns: TemplateColumns;
}

/**
 * Six ATS-friendly templates rendered by the single data-driven
 * CvDocumentRenderer (see cv-document-renderer.component.ts) - the same
 * CandidateProfile is never duplicated per template, only the CSS
 * variation keyed by [data-template] changes. All templates are plain
 * HTML/CSS text: no text-in-images, no decorative elements that would
 * interfere with ATS parsing.
 */
export const CV_TEMPLATES: TemplateDefinition[] = [
  {
    id: 'ats-classic',
    name: 'ATS Classic',
    description: 'Single column, plain hierarchy. The safest choice for automated screening.',
    columns: 1,
  },
  {
    id: 'ats-professional',
    name: 'ATS Professional',
    description: 'Single column with stronger visual hierarchy and a confident accent.',
    columns: 1,
  },
  {
    id: 'executive',
    name: 'Executive',
    description: 'Single column, generous whitespace, a refined premium register.',
    columns: 1,
  },
  {
    id: 'modern-split',
    name: 'Modern Split',
    description: 'Two columns: a compact sidebar for contact and skills, main content beside it.',
    columns: 2,
  },
  {
    id: 'technical',
    name: 'Technical',
    description: 'Two columns tuned for engineering roles, with a monospace technical accent.',
    columns: 2,
  },
  {
    id: 'minimal',
    name: 'Minimal',
    description: 'Single column, understated and quiet. No rules, no color, just structure.',
    columns: 1,
  },
];

export function findTemplate(id: string): TemplateDefinition {
  return CV_TEMPLATES.find((t) => t.id === id) ?? CV_TEMPLATES[0];
}
