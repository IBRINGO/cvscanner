import { CandidateProfile } from '../../cvs/models/candidate-profile.model';

/**
 * A clearly-labelled sample profile shown in the template gallery only
 * when the visitor has no processed CV yet - never presented as a real
 * candidate. Once a real CV exists, the gallery previews templates with
 * that person's own real data instead (see template-gallery.component).
 */
export const SAMPLE_PROFILE: CandidateProfile = {
  full_name: 'Alex Candidate',
  email: 'alex@example.com',
  phone: '+1 555 000 0000',
  location: 'Remote',
  links: [],
  summary: 'This is a sample profile so you can compare templates before uploading your own CV.',
  experiences: [
    {
      title: 'Product Engineer',
      company: 'Sample Company',
      start_date_raw: '2021',
      end_date_raw: null,
      description: 'Placeholder role used only to preview how experience entries look in this template.',
      achievements: ['Placeholder achievement line', 'Another placeholder achievement line'],
      technologies: [],
      seniority: null,
      evidence: null,
    },
  ],
  education: [
    {
      institution: 'Sample University',
      degree: 'BSc Example Field',
      field_of_study: null,
      start_date_raw: '2016',
      end_date_raw: '2020',
      degree_level: null,
      evidence: null,
    },
  ],
  projects: [],
  certifications: [],
  languages: [],
  skills: [
    { raw_text: 'Example Skill A', skill: null, evidence: null },
    { raw_text: 'Example Skill B', skill: null, evidence: null },
    { raw_text: 'Example Skill C', skill: null, evidence: null },
  ],
};
