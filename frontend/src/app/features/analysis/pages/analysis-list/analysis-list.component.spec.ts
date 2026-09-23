import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { of } from 'rxjs';
import { DocumentSummary } from '../../../../shared/models/document.model';
import { CvApiService } from '../../../cvs/services/cv-api.service';
import { JobApiService } from '../../../jobs/services/job-api.service';
import { AnalysisApiService } from '../../services/analysis-api.service';
import { AnalysisListComponent } from './analysis-list.component';

function document(overrides: Partial<DocumentSummary> = {}): DocumentSummary {
  return {
    id: '1',
    document_type: 'CV',
    original_filename: 'cv.pdf',
    mime_type: 'application/pdf',
    file_size: 10,
    status: 'PROCESSED',
    page_count: 1,
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
    ...overrides,
  };
}

describe('AnalysisListComponent', () => {
  let fixture: ComponentFixture<AnalysisListComponent>;
  let cvApiSpy: jasmine.SpyObj<CvApiService>;
  let jobApiSpy: jasmine.SpyObj<JobApiService>;
  let analysisApiSpy: jasmine.SpyObj<AnalysisApiService>;

  function setup(cvs: DocumentSummary[], jobs: DocumentSummary[]): void {
    cvApiSpy = jasmine.createSpyObj('CvApiService', ['list']);
    jobApiSpy = jasmine.createSpyObj('JobApiService', ['list']);
    analysisApiSpy = jasmine.createSpyObj('AnalysisApiService', ['list', 'createAnalysis']);
    cvApiSpy.list.and.returnValue(of(cvs));
    jobApiSpy.list.and.returnValue(of(jobs));
    analysisApiSpy.list.and.returnValue(of([]));

    TestBed.configureTestingModule({
      imports: [AnalysisListComponent],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([]),
        { provide: CvApiService, useValue: cvApiSpy },
        { provide: JobApiService, useValue: jobApiSpy },
        { provide: AnalysisApiService, useValue: analysisApiSpy },
      ],
    });
    fixture = TestBed.createComponent(AnalysisListComponent);
    fixture.detectChanges();
  }

  it('shows an empty state explaining what is needed when there are no processed documents', () => {
    setup([], []);
    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(text).toContain('You need at least one processed');
  });

  it('shows the creation form once at least one processed CV and job exist', () => {
    setup([document({ id: 'cv-1' })], [document({ id: 'job-1', document_type: 'JOB_OFFER' })]);
    expect((fixture.nativeElement as HTMLElement).querySelector('form')).not.toBeNull();
  });

  it('only lists PROCESSED documents in the pickers, not PENDING ones', () => {
    setup(
      [document({ id: 'cv-1', status: 'PROCESSED' }), document({ id: 'cv-2', status: 'PROCESSING' })],
      [document({ id: 'job-1', document_type: 'JOB_OFFER' })],
    );
    const options = (fixture.nativeElement as HTMLElement).querySelectorAll('select')[0].querySelectorAll('option');
    // one disabled placeholder + one processed CV
    expect(options.length).toBe(2);
  });

  it('shows an empty analyses list message with no history', () => {
    setup([document({ id: 'cv-1' })], [document({ id: 'job-1', document_type: 'JOB_OFFER' })]);
    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(text).toContain('No analyses yet');
  });
});
