export type RecommendationType =
  | 'MISSING_REQUIREMENT'
  | 'WEAK_EVIDENCE'
  | 'UNDERREPRESENTED_SKILL'
  | 'EXPERIENCE_CLARIFICATION'
  | 'KEYWORD_PLACEMENT'
  | 'RESPONSIBILITY_ALIGNMENT'
  | 'CERTIFICATION_GAP'
  | 'LANGUAGE_GAP'
  | 'SENIORITY_CLARIFICATION';

export type RecommendationPriority = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';

export type RecommendationConfidence = 'HIGH' | 'MEDIUM' | 'LOW';

export type RecommendationSafety =
  | 'SAFE_TO_REPHRASE'
  | 'SAFE_TO_REORDER'
  | 'REQUIRES_CANDIDATE_CONFIRMATION'
  | 'NOT_SAFE_TO_AUTOMATE';

export type RecommendationImpact = 'HIGH_IMPACT' | 'MEDIUM_IMPACT' | 'LOW_IMPACT';

export interface RecommendationEvidenceItem {
  text: string;
  page_number: number | null;
  section: string | null;
  confidence: number;
  extraction_method: string;
  source_type: string;
  source_label: string | null;
}

export interface Recommendation {
  id: string;
  type: RecommendationType;
  priority: RecommendationPriority;
  confidence: RecommendationConfidence;
  safety: RecommendationSafety;
  impact: RecommendationImpact;
  title: string;
  summary: string;
  reason: string;
  suggested_action: string;
  related_requirement: number | null;
  supporting_evidence: RecommendationEvidenceItem[];
  current_state: string | null;
  target_state: string | null;
  safe_to_tailor: boolean;
  created_at: string;
}
