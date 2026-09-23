import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { of } from 'rxjs';
import { DocumentSummary } from '../../../../shared/models/document.model';
import { AnalysisSummary } from '../../../analysis/models/analysis.model';
import { AnalysisApiService } from '../../../analysis/services/analysis-api.service';
import { CvApiService } from '../../../cvs/services/cv-api.service';
import { JobApiService } from '../../../jobs/services/job-api.service';
import { TailoringApiService } from '../../../tailoring/services/tailoring-api.service';
import { ApplicationListComponent } from './application-list.component';

function doc(overrides: Partial<DocumentSummary> = {}): DocumentSummary {
  return {
    id: 'cv-1',
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
    overall_score: 0.83,
    created_at: '2026-01-01T00:00:00Z',
    completed_at: '2026-01-01T00:00:00Z',
    ...overrides,
  };
}

describe('ApplicationListComponent', () => {
  let fixture: ComponentFixture<ApplicationListComponent>;

  function setup(cvs: DocumentSummary[], jobs: DocumentSummary[], analyses: AnalysisSummary[]): void {
    const cvApiSpy = jasmine.createSpyObj('CvApiService', { list: of(cvs) });
    const jobApiSpy = jasmine.createSpyObj('JobApiService', { list: of(jobs) });
    const analysisApiSpy = jasmine.createSpyObj('AnalysisApiService', { list: of(analyses) });
    const tailoringApiSpy = jasmine.createSpyObj('TailoringApiService', { list: of([]) });

    TestBed.configureTestingModule({
      imports: [ApplicationListComponent],
      providers: [
        provideRouter([]),
        { provide: CvApiService, useValue: cvApiSpy },
        { provide: JobApiService, useValue: jobApiSpy },
        { provide: AnalysisApiService, useValue: analysisApiSpy },
        { provide: TailoringApiService, useValue: tailoringApiSpy },
      ],
    });
    fixture = TestBed.createComponent(ApplicationListComponent);
    fixture.detectChanges();
  }

  it('shows an empty state pointing to the analysis flow when there are no applications', () => {
    setup([], [], []);
    expect((fixture.nativeElement as HTMLElement).textContent).toContain('No applications yet');
  });

  it('lists every real analysis as an application card', () => {
    setup(
      [doc({ id: 'cv-1' })],
      [doc({ id: 'job-1', document_type: 'JOB_OFFER' })],
      [analysis(), analysis({ id: 'analysis-2' })],
    );
    expect((fixture.nativeElement as HTMLElement).querySelectorAll('app-application-card').length).toBe(2);
  });
});
