import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { of } from 'rxjs';
import { CvApiService } from '../../../cvs/services/cv-api.service';
import { JobApiService } from '../../../jobs/services/job-api.service';
import { SkillApiService } from '../../../skills/services/skill-api.service';
import { HealthService } from '../../services/health.service';
import { DocumentSummary } from '../../../../shared/models/document.model';
import { DashboardPageComponent } from './dashboard-page.component';

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

describe('DashboardPageComponent', () => {
  let fixture: ComponentFixture<DashboardPageComponent>;
  let cvApiSpy: jasmine.SpyObj<CvApiService>;
  let jobApiSpy: jasmine.SpyObj<JobApiService>;
  let skillApiSpy: jasmine.SpyObj<SkillApiService>;

  function setup(cvs: DocumentSummary[], jobs: DocumentSummary[]): void {
    cvApiSpy = jasmine.createSpyObj('CvApiService', ['list']);
    jobApiSpy = jasmine.createSpyObj('JobApiService', ['list']);
    skillApiSpy = jasmine.createSpyObj('SkillApiService', ['list']);
    cvApiSpy.list.and.returnValue(of(cvs));
    jobApiSpy.list.and.returnValue(of(jobs));
    skillApiSpy.list.and.returnValue(
      of([
        { canonical_name: 'Python', category: 'PROGRAMMING_LANGUAGE', domain: 'SOFTWARE_DEVELOPMENT', description: null },
        { canonical_name: 'PostgreSQL', category: 'DATABASE', domain: 'DATA_AND_AI', description: null },
      ]),
    );

    TestBed.configureTestingModule({
      imports: [DashboardPageComponent],
      providers: [
        provideRouter([]),
        { provide: CvApiService, useValue: cvApiSpy },
        { provide: JobApiService, useValue: jobApiSpy },
        { provide: SkillApiService, useValue: skillApiSpy },
        { provide: HealthService, useValue: jasmine.createSpyObj('HealthService', { check: of({ status: 'ok', service: 'x', version: '1' }) }) },
      ],
    });
    fixture = TestBed.createComponent(DashboardPageComponent);
    fixture.detectChanges();
  }

  it('shows real counts of CVs and job offers, not fabricated statistics', () => {
    setup([doc({ id: 'a' }), doc({ id: 'b' })], [doc({ id: 'c', document_type: 'JOB_OFFER' })]);

    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(text).toContain('2');
    expect(text).toContain('CVs');
    expect(text).toContain('1');
    expect(text).toContain('Job offers');
  });

  it('shows an empty state with a call to action when there are no CVs', () => {
    setup([], []);

    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(text).toContain('No CVs yet');
    expect(text).toContain('Upload your first one');
  });

  it('counts failed documents as needing attention', () => {
    setup([doc({ id: 'a', status: 'FAILED' }), doc({ id: 'b', status: 'PROCESSED' })], []);

    const stat = Array.from((fixture.nativeElement as HTMLElement).querySelectorAll('.dashboard__stat')).find((el) =>
      el.textContent?.includes('Needs attention'),
    );
    expect(stat?.textContent).toContain('1');
  });

  it('groups skills by domain with real counts, not fake percentages', () => {
    setup([], []);

    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(text).toContain('Software Development');
    expect(text).toContain('Data And AI');
    expect(text).not.toMatch(/%/);
  });

  it('never renders a match score or compatibility indicator', () => {
    setup([doc()], [doc({ document_type: 'JOB_OFFER' })]);

    const text = (fixture.nativeElement as HTMLElement).textContent?.toLowerCase() ?? '';
    expect(text).not.toContain('match score');
    expect(text).not.toContain('compatibility');
  });
});
