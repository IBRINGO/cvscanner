export type StandardSectionKind =
  | 'summary'
  | 'experience'
  | 'education'
  | 'skills'
  | 'projects'
  | 'certifications'
  | 'languages';

export interface StandardSectionRef {
  id: StandardSectionKind;
  kind: StandardSectionKind;
}

export interface CustomSectionRef {
  id: string;
  kind: 'custom';
  title: string;
  content: string;
}

export type CvSectionRef = StandardSectionRef | CustomSectionRef;

export const DEFAULT_SECTION_ORDER: StandardSectionRef[] = [
  { id: 'summary', kind: 'summary' },
  { id: 'experience', kind: 'experience' },
  { id: 'education', kind: 'education' },
  { id: 'skills', kind: 'skills' },
  { id: 'projects', kind: 'projects' },
  { id: 'certifications', kind: 'certifications' },
  { id: 'languages', kind: 'languages' },
];

export const SECTION_LABELS: Record<string, string> = {
  summary: 'Summary',
  experience: 'Experience',
  education: 'Education',
  skills: 'Skills',
  projects: 'Projects',
  certifications: 'Certifications',
  languages: 'Languages',
};

/** Sections placed in the sidebar column for 2-column templates. */
export const SIDEBAR_SECTION_KINDS: ReadonlySet<string> = new Set(['skills', 'languages', 'certifications']);
