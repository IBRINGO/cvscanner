import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { Router, provideRouter } from '@angular/router';
import { of } from 'rxjs';
import { DocumentSummary } from '../../../../shared/models/document.model';
import { AnalysisApiService } from '../../../analysis/services/analysis-api.service';
import { CvApiService } from '../../../cvs/services/cv-api.service';
import { JobApiService } from '../../../jobs/services/job-api.service';
import { NewApplicationComponent } from './new-application.component';

function doc(overrides: Partial<DocumentSummary> = {}): DocumentSummary {
  return {
    id: 'doc-1',
    document_type: 'CV',
    original_filename: 'cv.pdf',
    mime_type: 'application/pdf',
    file_size: 100,
    status: 'UPLOADED',
    page_count: 1,
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
    ...overrides,
  };
}

describe('NewApplicationComponent', () => {
  let fixture: ComponentFixture<NewApplicationComponent>;
  let cvApiSpy: jasmine.SpyObj<CvApiService>;
  let jobApiSpy: jasmine.SpyObj<JobApiService>;
  let analysisApiSpy: jasmine.SpyObj<AnalysisApiService>;
  let router: Router;

  function setup(): void {
    cvApiSpy = jasmine.createSpyObj('CvApiService', ['upload', 'getStatus']);
    jobApiSpy = jasmine.createSpyObj('JobApiService', ['uploadFile', 'uploadText', 'getStatus']);
    analysisApiSpy = jasmine.createSpyObj('AnalysisApiService', ['createAnalysis']);

    TestBed.configureTestingModule({
      imports: [NewApplicationComponent],
      providers: [
        provideRouter([]),
        { provide: CvApiService, useValue: cvApiSpy },
        { provide: JobApiService, useValue: jobApiSpy },
        { provide: AnalysisApiService, useValue: analysisApiSpy },
      ],
    });
    fixture = TestBed.createComponent(NewApplicationComponent);
    router = TestBed.inject(Router);
    spyOn(router, 'navigate');
    fixture.detectChanges();
  }

  it('auto-advances to the job step only once CV processing reaches a real terminal status', fakeAsync(() => {
    setup();
    cvApiSpy.upload.and.returnValue(of(doc({ id: 'cv-1' })));
    cvApiSpy.getStatus.and.returnValue(of({ id: 'cv-1', status: 'PROCESSED', error: null, updated_at: 'x' }));

    fixture.componentInstance.onCvFileSelected(new File([], 'cv.pdf'));
    fixture.detectChanges();

    expect(fixture.componentInstance.step()).toBe('cv');
    tick(1400);
    expect(fixture.componentInstance.step()).toBe('job');
  }));

  it('shows the real backend error and lets the user retry when CV processing fails', fakeAsync(() => {
    setup();
    cvApiSpy.upload.and.returnValue(of(doc({ id: 'cv-1' })));
    cvApiSpy.getStatus.and.returnValue(
      of({ id: 'cv-1', status: 'FAILED', error: 'Unreadable PDF', updated_at: 'x' }),
    );

    fixture.componentInstance.onCvFileSelected(new File([], 'cv.pdf'));
    fixture.detectChanges();
    tick(1400);

    expect(fixture.componentInstance.step()).toBe('cv');
    expect(fixture.componentInstance.cvError()).toBe('Unreadable PDF');

    fixture.componentInstance.resetCv();
    expect(fixture.componentInstance.cvDocument()).toBeNull();
  }));

  it('creates the analysis and navigates there once both documents are processed', fakeAsync(() => {
    setup();
    cvApiSpy.upload.and.returnValue(of(doc({ id: 'cv-1' })));
    cvApiSpy.getStatus.and.returnValue(of({ id: 'cv-1', status: 'PROCESSED', error: null, updated_at: 'x' }));
    jobApiSpy.uploadText.and.returnValue(
      of(doc({ id: 'job-1', document_type: 'JOB_OFFER', original_filename: 'job.txt' })),
    );
    jobApiSpy.getStatus.and.returnValue(of({ id: 'job-1', status: 'PROCESSED', error: null, updated_at: 'x' }));
    analysisApiSpy.createAnalysis.and.returnValue(
      of({
        id: 'analysis-1',
        candidate_document_id: 'cv-1',
        job_document_id: 'job-1',
        status: 'PENDING',
        engine_version: '1.0.0',
        overall_score: null,
        created_at: 'x',
        completed_at: null,
      }),
    );

    fixture.componentInstance.onCvFileSelected(new File([], 'cv.pdf'));
    fixture.detectChanges();
    tick(1400);
    expect(fixture.componentInstance.step()).toBe('job');

    fixture.componentInstance.jobText = 'Some job posting';
    fixture.componentInstance.submitJobText();
    fixture.detectChanges();
    tick(1400);

    expect(analysisApiSpy.createAnalysis).toHaveBeenCalledWith('cv-1', 'job-1');
    expect(router.navigate).toHaveBeenCalledWith(['/analysis', 'analysis-1']);
  }));

  it('never advances to job on a non-terminal status, so no partial progress is faked', fakeAsync(() => {
    setup();
    cvApiSpy.upload.and.returnValue(of(doc({ id: 'cv-1' })));
    cvApiSpy.getStatus.and.returnValue(of({ id: 'cv-1', status: 'PROCESSING', error: null, updated_at: 'x' }));

    fixture.componentInstance.onCvFileSelected(new File([], 'cv.pdf'));
    fixture.detectChanges();
    tick(5000);

    expect(fixture.componentInstance.step()).toBe('cv');
    fixture.destroy();
  }));
});
