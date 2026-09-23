export type TailoringMode = 'CONSERVATIVE' | 'AGGRESSIVE_SAFE';

export type TailoringStatus = 'PENDING' | 'PLANNING' | 'GENERATING' | 'VALIDATING' | 'COMPLETED' | 'FAILED';

export type ChangeType = 'ADDED' | 'REMOVED' | 'UNCHANGED';

export interface DiffSegment {
  text: string;
  change_type: ChangeType;
}

export interface TailoringChange {
  fact_id: string;
  recommendation_title: string;
  original_text: string;
  final_text: string;
  diff: DiffSegment[];
  accepted: boolean;
  rejection_reasons: string[];
}

export interface SectionOperation {
  fact_id: string;
  transformation: string;
  recommendation_title: string;
  target_state: string | null;
}

export interface TailoringPlanSummary {
  id: string;
  analysis_id: string;
  mode: TailoringMode;
  engine_version: string;
  status: TailoringStatus;
  before_score: number | null;
  after_score: number | null;
  created_at: string;
  completed_at: string | null;
}

export interface TailoringPlanDetail extends TailoringPlanSummary {
  operations: SectionOperation[];
  protected_fact_ids: string[];
  requirements_improved: number;
  requirements_unchanged: number;
  requirements_still_missing: number;
  changes: TailoringChange[];
  error_message: string | null;
}

export interface TailoringStatusResponse {
  id: string;
  status: TailoringStatus;
  error: string | null;
  completed_at: string | null;
}
