import { DocumentSummary } from '../../../shared/models/document.model';
import { AnalysisSummary } from '../../analysis/models/analysis.model';
import { TailoringPlanSummary } from '../../tailoring/models/tailoring.model';
import { buildApplications, findOrphanDocuments } from './build-applications';

function doc(overrides: Partial<DocumentSummary> = {}): DocumentSummary {
  return {
    id: 'doc-1',
    document_type: 'CV',
    original_filename: 'resume.pdf',
    mime_type: 'application/pdf',
    file_size: 1024,
    status: 'PROCESSED',
    page_count: 1,
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
    ...overrides,
  };
}

function analysis(overrides: Partial<AnalysisSummary> = {}): AnalysisSummary {
  return {
    id: 'analysis-1',
    candidate_document_id: 'cv-1',
    job_document_id: 'job-1',
    status: 'COMPLETED',
    engine_version: '1.0.0',
    overall_score: 0.83,
    created_at: '2026-01-02T00:00:00Z',
    completed_at: '2026-01-02T00:01:00Z',
    ...overrides,
  };
}

function plan(overrides: Partial<TailoringPlanSummary> = {}): TailoringPlanSummary {
  return {
    id: 'plan-1',
    analysis_id: 'analysis-1',
    mode: 'CONSERVATIVE',
    engine_version: '1.0.0',
    status: 'COMPLETED',
    before_score: 0.7,
    after_score: 0.83,
    created_at: '2026-01-03T00:00:00Z',
    completed_at: '2026-01-03T00:01:00Z',
    ...overrides,
  };
}

describe('buildApplications', () => {
  const cvs = [doc({ id: 'cv-1', original_filename: 'my-cv.pdf' })];
  const jobs = [doc({ id: 'job-1', document_type: 'JOB_OFFER', original_filename: 'job.pdf' })];

  it('never fabricates an application when the referenced documents do not exist', () => {
    const result = buildApplications([], [], [analysis()], []);
    expect(result).toEqual([]);
  });

  it('points an in-progress analysis at the analysis stage', () => {
    const [app] = buildApplications(cvs, jobs, [analysis({ status: 'PROCESSING' })], []);
    expect(app.stage).toBe('analysis');
    expect(app.completedStages).toEqual(['cv', 'job']);
    expect(app.nextActionLink).toEqual(['/analysis', 'analysis-1']);
  });

  it('points a completed analysis with no tailoring plan at recommendations', () => {
    const [app] = buildApplications(cvs, jobs, [analysis()], []);
    expect(app.stage).toBe('recommendations');
    expect(app.nextActionLink).toEqual(['/analysis', 'analysis-1', 'recommendations']);
  });

  it('points a completed tailoring plan at export/view', () => {
    const [app] = buildApplications(cvs, jobs, [analysis()], [plan()]);
    expect(app.stage).toBe('export');
    expect(app.nextActionLink).toEqual(['/tailoring', 'plan-1']);
  });

  it('points an in-progress tailoring plan at tailoring progress', () => {
    const [app] = buildApplications(cvs, jobs, [analysis()], [plan({ status: 'GENERATING' })]);
    expect(app.stage).toBe('tailoring');
    expect(app.nextActionLabel).toBe('View tailoring progress');
  });

  it('uses only the most recent tailoring plan when several exist for one analysis', () => {
    const plans = [
      plan({ id: 'plan-old', status: 'FAILED', created_at: '2026-01-02T12:00:00Z' }),
      plan({ id: 'plan-new', status: 'COMPLETED', created_at: '2026-01-03T12:00:00Z' }),
    ];
    const [app] = buildApplications(cvs, jobs, [analysis()], plans);
    expect(app.tailoringPlan?.id).toBe('plan-new');
  });

  it('sorts applications by most recently created analysis first', () => {
    const analyses = [
      analysis({ id: 'older', created_at: '2026-01-01T00:00:00Z' }),
      analysis({ id: 'newer', created_at: '2026-01-05T00:00:00Z' }),
    ];
    const result = buildApplications(cvs, jobs, analyses, []);
    expect(result.map((a) => a.analysisId)).toEqual(['newer', 'older']);
  });
});

describe('findOrphanDocuments', () => {
  it('finds processed CVs and jobs not referenced by any analysis', () => {
    const cvs = [doc({ id: 'cv-used' }), doc({ id: 'cv-free' })];
    const jobs = [doc({ id: 'job-used', document_type: 'JOB_OFFER' })];
    const analyses = [analysis({ candidate_document_id: 'cv-used', job_document_id: 'job-used' })];

    const result = findOrphanDocuments(cvs, jobs, analyses);
    expect(result.cvs.map((d) => d.id)).toEqual(['cv-free']);
    expect(result.jobs).toEqual([]);
  });

  it('excludes documents that are not yet processed, even if unused', () => {
    const cvs = [doc({ id: 'cv-pending', status: 'PROCESSING' })];
    const result = findOrphanDocuments(cvs, [], []);
    expect(result.cvs).toEqual([]);
  });
});
