import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { of } from 'rxjs';
import { DocumentSummary } from '../../../../shared/models/document.model';
import { CandidateProfile } from '../../../cvs/models/candidate-profile.model';
import { CvApiService } from '../../../cvs/services/cv-api.service';
import { TemplateGalleryComponent } from './template-gallery.component';

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

function profile(overrides: Partial<CandidateProfile> = {}): CandidateProfile {
  return {
    full_name: 'Jordan Rivera',
    email: null,
    phone: null,
    location: null,
    links: [],
    summary: null,
    experiences: [],
    education: [],
    projects: [],
    certifications: [],
    languages: [],
    skills: [],
    ...overrides,
  };
}

describe('TemplateGalleryComponent', () => {
  let fixture: ComponentFixture<TemplateGalleryComponent>;

  function setup(cvs: DocumentSummary[], profileResponse?: CandidateProfile): void {
    const cvApiSpy = jasmine.createSpyObj('CvApiService', ['list', 'getProfile']);
    cvApiSpy.list.and.returnValue(of(cvs));
    cvApiSpy.getProfile.and.returnValue(
      of({ document_id: 'cv-1', status: 'PROCESSED', profile: profileResponse ?? null }),
    );

    TestBed.configureTestingModule({
      imports: [TemplateGalleryComponent],
      providers: [provideRouter([]), { provide: CvApiService, useValue: cvApiSpy }],
    });
    fixture = TestBed.createComponent(TemplateGalleryComponent);
    fixture.detectChanges();
  }

  it('renders all six templates', () => {
    setup([]);
    expect((fixture.nativeElement as HTMLElement).querySelectorAll('.gallery__card').length).toBe(6);
  });

  it('falls back to a clearly-labelled sample profile when no processed CV exists', () => {
    setup([]);
    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(text).toContain('sample data');
    expect(text).toContain('Alex Candidate');
  });

  it('previews with the real most-recent processed CV once one is available', () => {
    setup([doc({ id: 'cv-1', status: 'PROCESSED' })], profile({ full_name: 'Jordan Rivera' }));
    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(text).toContain('Jordan Rivera');
    expect(text).not.toContain('sample data');
  });

  it('ignores CVs that are not yet processed when picking a preview profile', () => {
    setup([doc({ id: 'cv-pending', status: 'PROCESSING' })]);
    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(text).toContain('sample data');
  });
});
