import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { DocumentSummary } from '../../../../shared/models/document.model';
import { ApplicationView } from '../../models/application.model';
import { ApplicationCardComponent } from './application-card.component';

function doc(overrides: Partial<DocumentSummary> = {}): DocumentSummary {
  return {
    id: 'doc-1',
    document_type: 'CV',
    original_filename: 'my-cv.pdf',
    mime_type: 'application/pdf',
    file_size: 1024,
    status: 'PROCESSED',
    page_count: 1,
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
    ...overrides,
  };
}

function appView(overrides: Partial<ApplicationView> = {}): ApplicationView {
  return {
    analysisId: 'analysis-1',
    cv: doc(),
    job: doc({ id: 'job-1', document_type: 'JOB_OFFER', original_filename: 'job.pdf' }),
    analysisStatus: 'COMPLETED',
    score: 0.83,
    tailoringPlan: null,
    stage: 'recommendations',
    completedStages: ['cv', 'job', 'analysis'],
    nextActionLabel: 'Review recommendations',
    nextActionLink: ['/analysis', 'analysis-1', 'recommendations'],
    createdAt: '2026-01-01T00:00:00Z',
    ...overrides,
  };
}

describe('ApplicationCardComponent', () => {
  let fixture: ComponentFixture<ApplicationCardComponent>;

  function setup(app: ApplicationView): void {
    TestBed.configureTestingModule({
      imports: [ApplicationCardComponent],
      providers: [provideRouter([])],
    });
    fixture = TestBed.createComponent(ApplicationCardComponent);
    fixture.componentInstance.app = app;
    fixture.detectChanges();
  }

  it('shows the real CV and job filenames', () => {
    setup(appView());
    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(text).toContain('my-cv.pdf');
    expect(text).toContain('job.pdf');
  });

  it('renders the rounded real score with no fabricated precision', () => {
    setup(appView({ score: 0.831 }));
    expect((fixture.nativeElement as HTMLElement).textContent).toContain('83');
  });

  it('falls back to the analysis status when there is no score yet', () => {
    setup(appView({ score: null, analysisStatus: 'PROCESSING' }));
    expect((fixture.nativeElement as HTMLElement).textContent).toContain('PROCESSING');
  });

  it('links the next action to the real next-action route', () => {
    setup(appView());
    const link = (fixture.nativeElement as HTMLElement).querySelector('.app-card__action');
    expect(link?.getAttribute('href')).toBe('/analysis/analysis-1/recommendations');
  });
});
