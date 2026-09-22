import { Evidence, SkillRef } from '../../../shared/models/evidence.model';
import { ProcessingStatus } from '../../../shared/models/document.model';

export interface Experience {
  title: string | null;
  company: string | null;
  start_date_raw: string | null;
  end_date_raw: string | null;
  description: string | null;
  achievements: string[];
  technologies: string[];
  evidence: Evidence | null;
}

export interface Education {
  institution: string | null;
  degree: string | null;
  field_of_study: string | null;
  start_date_raw: string | null;
  end_date_raw: string | null;
  evidence: Evidence | null;
}

export interface Project {
  name: string;
  description: string | null;
  technologies: string[];
}

export interface Certification {
  name: string;
  issuer: string | null;
  date_raw: string | null;
  evidence: Evidence | null;
}

export interface Language {
  name: string;
  proficiency: string | null;
}

export interface CandidateSkill {
  raw_text: string;
  skill: SkillRef | null;
  evidence: Evidence | null;
}

export interface CandidateProfile {
  full_name: string | null;
  email: string | null;
  phone: string | null;
  location: string | null;
  links: string[];
  summary: string | null;
  experiences: Experience[];
  education: Education[];
  projects: Project[];
  certifications: Certification[];
  languages: Language[];
  skills: CandidateSkill[];
}

export interface CvProfileResponse {
  document_id: string;
  status: ProcessingStatus;
  profile: CandidateProfile | null;
}
