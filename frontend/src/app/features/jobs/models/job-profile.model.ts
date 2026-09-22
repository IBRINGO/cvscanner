import { Evidence, SkillRef } from '../../../shared/models/evidence.model';
import { ProcessingStatus } from '../../../shared/models/document.model';

export type RequirementType =
  | 'REQUIRED_SKILL'
  | 'PREFERRED_SKILL'
  | 'EXPERIENCE'
  | 'EDUCATION'
  | 'CERTIFICATION'
  | 'LANGUAGE'
  | 'RESPONSIBILITY'
  | 'SENIORITY'
  | 'OTHER';

export type RequirementImportance = 'REQUIRED' | 'PREFERRED';

export interface JobRequirement {
  requirement_type: RequirementType;
  importance: RequirementImportance;
  raw_text: string;
  skill: SkillRef | null;
  evidence: Evidence | null;
}

export interface JobProfile {
  title: string | null;
  company: string | null;
  location: string | null;
  employment_type: string | null;
  seniority: string | null;
  summary: string | null;
  responsibilities: string[];
  requirements: JobRequirement[];
}

export interface JobProfileResponse {
  document_id: string;
  status: ProcessingStatus;
  profile: JobProfile | null;
}
