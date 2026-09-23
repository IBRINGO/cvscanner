import { DocumentSummary } from '../../../shared/models/document.model';
import { AnalysisSummary } from '../../analysis/models/analysis.model';
import { TailoringPlanSummary } from '../../tailoring/models/tailoring.model';
import { ApplicationView, OrphanDocuments } from '../models/application.model';

/**
 * Derives the "Applications" view from the real records that already
 * exist (CVs, jobs, analyses, tailoring plans) - no new backend entity,
 * no invented pairing. Every application shown here corresponds to a
 * real Analysis row; a CV or job without an analysis never becomes a
 * fabricated "application", it surfaces separately via
 * `findOrphanDocuments` instead.
 */
export function buildApplications(
  cvs: DocumentSummary[],
  jobs: DocumentSummary[],
  analyses: AnalysisSummary[],
  tailoringPlans: TailoringPlanSummary[],
): ApplicationView[] {
  const cvById = new Map(cvs.map((doc) => [doc.id, doc]));
  const jobById = new Map(jobs.map((doc) => [doc.id, doc]));
  const latestPlanByAnalysis = new Map<string, TailoringPlanSummary>();
  for (const plan of tailoringPlans) {
    const existing = latestPlanByAnalysis.get(plan.analysis_id);
    if (!existing || plan.created_at > existing.created_at) {
      latestPlanByAnalysis.set(plan.analysis_id, plan);
    }
  }

  const views: ApplicationView[] = [];
  for (const analysis of analyses) {
    const cv = cvById.get(analysis.candidate_document_id);
    const job = jobById.get(analysis.job_document_id);
    if (!cv || !job) continue;

    const tailoringPlan = latestPlanByAnalysis.get(analysis.id) ?? null;
    const { stage, completedStages, nextActionLabel, nextActionLink } = deriveStage(analysis, tailoringPlan);

    views.push({
      analysisId: analysis.id,
      cv,
      job,
      analysisStatus: analysis.status,
      score: analysis.overall_score,
      tailoringPlan,
      stage,
      completedStages,
      nextActionLabel,
      nextActionLink,
      createdAt: analysis.created_at,
    });
  }

  return views.sort((a, b) => (a.createdAt < b.createdAt ? 1 : -1));
}

function deriveStage(
  analysis: AnalysisSummary,
  tailoringPlan: TailoringPlanSummary | null,
): Pick<ApplicationView, 'stage' | 'completedStages' | 'nextActionLabel' | 'nextActionLink'> {
  if (analysis.status === 'PENDING' || analysis.status === 'PROCESSING') {
    return {
      stage: 'analysis',
      completedStages: ['cv', 'job'],
      nextActionLabel: 'View analysis progress',
      nextActionLink: ['/analysis', analysis.id],
    };
  }
  if (analysis.status === 'FAILED') {
    return {
      stage: 'analysis',
      completedStages: ['cv', 'job'],
      nextActionLabel: 'Review analysis error',
      nextActionLink: ['/analysis', analysis.id],
    };
  }

  // analysis.status === 'COMPLETED' from here on.
  if (!tailoringPlan) {
    return {
      stage: 'recommendations',
      completedStages: ['cv', 'job', 'analysis'],
      nextActionLabel: 'Review recommendations',
      nextActionLink: ['/analysis', analysis.id, 'recommendations'],
    };
  }
  if (tailoringPlan.status === 'COMPLETED') {
    return {
      stage: 'export',
      completedStages: ['cv', 'job', 'analysis', 'recommendations', 'tailoring'],
      nextActionLabel: 'View tailored CV',
      nextActionLink: ['/tailoring', tailoringPlan.id],
    };
  }
  if (tailoringPlan.status === 'FAILED') {
    return {
      stage: 'tailoring',
      completedStages: ['cv', 'job', 'analysis', 'recommendations'],
      nextActionLabel: 'Review tailoring error',
      nextActionLink: ['/tailoring', tailoringPlan.id],
    };
  }
  return {
    stage: 'tailoring',
    completedStages: ['cv', 'job', 'analysis', 'recommendations'],
    nextActionLabel: 'View tailoring progress',
    nextActionLink: ['/tailoring', tailoringPlan.id],
  };
}

/**
 * CVs/jobs that are ready to use but not yet part of any analysis -
 * shown as "ready to start" prompts, never folded into the applications
 * list as a fabricated pairing.
 */
export function findOrphanDocuments(
  cvs: DocumentSummary[],
  jobs: DocumentSummary[],
  analyses: AnalysisSummary[],
): OrphanDocuments {
  const usedCvIds = new Set(analyses.map((a) => a.candidate_document_id));
  const usedJobIds = new Set(analyses.map((a) => a.job_document_id));
  return {
    cvs: cvs.filter((doc) => doc.status === 'PROCESSED' && !usedCvIds.has(doc.id)),
    jobs: jobs.filter((doc) => doc.status === 'PROCESSED' && !usedJobIds.has(doc.id)),
  };
}
