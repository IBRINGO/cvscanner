import { ApplicationStage } from '../../../shared/components/ui/application-progress/application-progress.component';
import { DocumentSummary } from '../../../shared/models/document.model';
import { AnalysisStatus } from '../../analysis/models/analysis.model';
import { TailoringPlanSummary } from '../../tailoring/models/tailoring.model';

/**
 * "Application" is not a backend entity - CVScanner never introduced one.
 * An application is a candidate CV paired with a target job, which only
 * becomes a real, addressable pairing once an Analysis links them. This
 * view is derived client-side by joining Analysis -> CV/Job -> Tailoring,
 * never persisted, never fabricated when the underlying records don't
 * exist.
 */
export interface ApplicationView {
  analysisId: string;
  cv: DocumentSummary;
  job: DocumentSummary;
  analysisStatus: AnalysisStatus;
  score: number | null;
  tailoringPlan: TailoringPlanSummary | null;
  stage: ApplicationStage;
  completedStages: ApplicationStage[];
  nextActionLabel: string;
  nextActionLink: string[];
  createdAt: string;
}

export interface OrphanDocuments {
  cvs: DocumentSummary[];
  jobs: DocumentSummary[];
}
