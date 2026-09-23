import { ProcessingStatus } from '../../../shared/models/document.model';

export type AnalysisStatus = 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED';

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

export type RequirementPriority = 'MANDATORY' | 'PREFERRED' | 'OPTIONAL';

export type RequirementStatus = 'MET' | 'PARTIALLY_MET' | 'NOT_MET' | 'UNKNOWN';

export type MatchSignal =
  | 'EXACT_MATCH'
  | 'ALIAS_MATCH'
  | 'RELATED_MATCH'
  | 'SEMANTIC_MATCH'
  | 'PARTIAL_MATCH'
  | 'NO_EVIDENCE';

export type MatchStrength = 'NONE' | 'WEAK' | 'PARTIAL' | 'GOOD' | 'STRONG';

export interface MatchEvidenceItem {
  text: string;
  page_number: number | null;
  section: string | null;
  confidence: number;
  extraction_method: string;
  source_type: string;
  source_label: string | null;
}

export interface RequirementEvaluation {
  requirement_type: RequirementType;
  priority: RequirementPriority;
  raw_text: string;
  status: RequirementStatus;
  match_signal: MatchSignal;
  match_strength: MatchStrength;
  score: number;
  confidence: number;
  matched_skill: string | null;
  explanation: string;
  evidence: MatchEvidenceItem[];
}

export interface Gap {
  requirement_type: RequirementType;
  priority: RequirementPriority;
  raw_text: string;
  reason: string;
  evidence_status: string;
  related_candidate_skills: string[];
  confidence: number;
}

export interface DimensionScore {
  name: string;
  score: number;
  weight: number;
  evaluation_count: number;
}

export interface ScoreBreakdown {
  overall: number;
  skills: number;
  experience: number;
  seniority: number;
  education: number;
  certifications: number;
  languages: number;
  responsibilities: number;
  domain: number;
  mandatory_gap_penalty: number;
  dimensions: DimensionScore[];
}

export interface RequirementSummary {
  total: number;
  met: number;
  partially_met: number;
  not_met: number;
  unknown: number;
}

export interface AnalysisSummary {
  id: string;
  candidate_document_id: string;
  job_document_id: string;
  status: AnalysisStatus;
  engine_version: string;
  overall_score: number | null;
  created_at: string;
  completed_at: string | null;
}

export interface AnalysisDetail extends AnalysisSummary {
  score_breakdown: ScoreBreakdown | null;
  requirement_summary: RequirementSummary;
  requirement_evaluations: RequirementEvaluation[];
  gaps: Gap[];
  error_message: string | null;
}

export interface AnalysisStatusResponse {
  id: string;
  status: AnalysisStatus;
  error: string | null;
  completed_at: string | null;
}

/** Re-exported for convenience where a candidate/job picker needs to
 * filter to only fully processed documents. */
export type { ProcessingStatus };
