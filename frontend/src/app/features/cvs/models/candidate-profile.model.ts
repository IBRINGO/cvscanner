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
  seniority: SeniorityLevel | null;
  evidence: Evidence | null;
}

export type SeniorityLevel =
  | 'INTERN'
  | 'JUNIOR'
  | 'MID'
  | 'SENIOR'
  | 'LEAD'
  | 'MANAGER'
  | 'DIRECTOR'
  | 'EXECUTIVE'
  | 'UNKNOWN';

export type EducationLevel =
  | 'HIGH_SCHOOL'
  | 'ASSOCIATE'
  | 'BACHELOR'
  | 'MASTER'
  | 'DOCTORATE'
  | 'PROFESSIONAL_CERTIFICATE'
  | 'UNKNOWN';

export type LanguageProficiency =
  | 'BEGINNER'
  | 'ELEMENTARY'
  | 'INTERMEDIATE'
  | 'UPPER_INTERMEDIATE'
  | 'ADVANCED'
  | 'FLUENT'
  | 'NATIVE'
  | 'UNKNOWN';

export interface Education {
  institution: string | null;
  degree: string | null;
  field_of_study: string | null;
  start_date_raw: string | null;
  end_date_raw: string | null;
  degree_level: EducationLevel | null;
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
  canonical_name: string | null;
  proficiency_normalized: LanguageProficiency | null;
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
