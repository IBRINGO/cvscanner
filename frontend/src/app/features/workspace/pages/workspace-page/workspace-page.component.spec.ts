import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { of } from 'rxjs';
import { DocumentSummary } from '../../../../shared/models/document.model';
import { AnalysisSummary } from '../../../analysis/models/analysis.model';
import { AnalysisApiService } from '../../../analysis/services/analysis-api.service';
import { CvApiService } from '../../../cvs/services/cv-api.service';
import { JobApiService } from '../../../jobs/services/job-api.service';
import { SkillApiService } from '../../../skills/services/skill-api.service';
import { TailoringApiService } from '../../../tailoring/services/tailoring-api.service';
import { HealthService } from '../../services/health.service';
import { WorkspacePageComponent } from './workspace-page.component';

function doc(overrides: Partial<DocumentSummary> = {}): DocumentSummary {
  return {
    id: '1',
    document_type: 'CV',
    original_filename: 'cv.pdf',
    mime_type: 'application/pdf',
    file_size: 100,
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
    overall_score: 0.72,
    created_at: '2026-01-01T00:00:00Z',
    completed_at: '2026-01-01T00:00:00Z',
    ...overrides,
  };
}

describe('WorkspacePageComponent', () => {
  let fixture: ComponentFixture<WorkspacePageComponent>;

  function setup(options: {
    cvs?: DocumentSummary[];
    jobs?: DocumentSummary[];
    analyses?: AnalysisSummary[];
  }): void {
    const cvApiSpy = jasmine.createSpyObj('CvApiService', ['list']);
    const jobApiSpy = jasmine.createSpyObj('JobApiService', ['list']);
    const skillApiSpy = jasmine.createSpyObj('SkillApiService', ['list']);
    const analysisApiSpy = jasmine.createSpyObj('AnalysisApiService', ['list']);
    const tailoringApiSpy = jasmine.createSpyObj('TailoringApiService', ['list']);

    cvApiSpy.list.and.returnValue(of(options.cvs ?? []));
    jobApiSpy.list.and.returnValue(of(options.jobs ?? []));
    analysisApiSpy.list.and.returnValue(of(options.analyses ?? []));
    tailoringApiSpy.list.and.returnValue(of([]));
    skillApiSpy.list.and.returnValue(
      of([
        { canonical_name: 'Python', category: 'PROGRAMMING_LANGUAGE', domain: 'SOFTWARE_DEVELOPMENT', description: null },
        { canonical_name: 'PostgreSQL', category: 'DATABASE', domain: 'DATA_AND_AI', description: null },
      ]),
    );

    TestBed.configureTestingModule({
      imports: [WorkspacePageComponent],
      providers: [
        provideRouter([]),
        { provide: CvApiService, useValue: cvApiSpy },
        { provide: JobApiService, useValue: jobApiSpy },
        { provide: SkillApiService, useValue: skillApiSpy },
        { provide: AnalysisApiService, useValue: analysisApiSpy },
        { provide: TailoringApiService, useValue: tailoringApiSpy },
        {
          provide: HealthService,
          useValue: jasmine.createSpyObj('HealthService', {
            check: of({ status: 'ok', service: 'x', version: '1' }),
          }),
        },
      ],
    });
    fixture = TestBed.createComponent(WorkspacePageComponent);
    fixture.detectChanges();
  }

  it('shows an empty state pointing to the analysis flow when there are no applications', () => {
    setup({});
    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(text).toContain('No applications yet');
  });

  it('renders one application card per real analysis, joined to its real documents', () => {
    setup({
      cvs: [doc({ id: 'cv-1', original_filename: 'jordan.pdf' })],
      jobs: [doc({ id: 'job-1', document_type: 'JOB_OFFER', original_filename: 'backend-role.pdf' })],
      analyses: [analysis()],
    });
    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(text).toContain('jordan.pdf');
    expect(text).toContain('backend-role.pdf');
    expect(text).toContain('72');
    expect((fixture.nativeElement as HTMLElement).querySelectorAll('app-application-card').length).toBe(1);
  });

  it('surfaces processed documents with no analysis yet as "ready to pair", not as a fake application', () => {
    setup({
      cvs: [doc({ id: 'cv-orphan', original_filename: 'unused-cv.pdf' })],
      jobs: [],
      analyses: [],
    });
    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(text).toContain('Ready to pair');
    expect(text).toContain('unused-cv.pdf');
    expect((fixture.nativeElement as HTMLElement).querySelectorAll('app-application-card').length).toBe(0);
  });

  it('groups skills by domain with real counts, not fake percentages', () => {
    setup({});
    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(text).toContain('Software Development');
    expect(text).toContain('Data And AI');
    expect(text).not.toMatch(/%/);
  });

  it('shows an empty state for recent CVs when none exist', () => {
    setup({});
    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(text).toContain('No CVs yet');
    expect(text).toContain('Upload your first one');
  });
});
