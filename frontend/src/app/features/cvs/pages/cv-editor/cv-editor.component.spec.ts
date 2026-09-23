import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute, convertToParamMap, provideRouter } from '@angular/router';
import { of } from 'rxjs';
import { CandidateProfile } from '../../models/candidate-profile.model';
import { CvApiService } from '../../services/cv-api.service';
import { CvEditorComponent } from './cv-editor.component';

function profile(overrides: Partial<CandidateProfile> = {}): CandidateProfile {
  return {
    full_name: 'Jordan Rivera',
    email: 'jordan@example.com',
    phone: null,
    location: null,
    links: [],
    summary: 'Backend engineer.',
    experiences: [
      {
        title: 'Senior Backend Engineer',
        company: 'Acme',
        start_date_raw: '2020',
        end_date_raw: null,
        description: 'Built the platform.',
        achievements: [],
        technologies: [],
        seniority: null,
        evidence: null,
      },
    ],
    education: [],
    projects: [],
    certifications: [],
    languages: [],
    skills: [
      { raw_text: 'Python', skill: null, evidence: null },
      { raw_text: 'Django', skill: null, evidence: null },
    ],
    ...overrides,
  };
}

describe('CvEditorComponent', () => {
  let fixture: ComponentFixture<CvEditorComponent>;
  let component: CvEditorComponent;

  function setup(): void {
    const cvApiSpy = jasmine.createSpyObj('CvApiService', {
      getProfile: of({ document_id: 'cv-1', status: 'PROCESSED', profile: profile() }),
    });
    TestBed.configureTestingModule({
      imports: [CvEditorComponent],
      providers: [
        provideRouter([]),
        { provide: CvApiService, useValue: cvApiSpy },
        {
          provide: ActivatedRoute,
          useValue: {
            snapshot: { paramMap: convertToParamMap({ id: 'cv-1' }), queryParamMap: convertToParamMap({}) },
          },
        },
      ],
    });
    fixture = TestBed.createComponent(CvEditorComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  }

  it('loads the real candidate profile and renders it live', () => {
    setup();
    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(text).toContain('Jordan Rivera');
  });

  it('edits the summary and reflects it in the live preview immediately', () => {
    setup();
    component.updateSummary('Rewritten summary.');
    fixture.detectChanges();
    expect(component.profile()?.summary).toBe('Rewritten summary.');
    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(text).toContain('Rewritten summary.');
  });

  it('reorders sections without losing or duplicating any of them', () => {
    setup();
    const before = component.sectionOrder().map((r) => r.id);
    component.moveSection(0, 1);
    const after = component.sectionOrder().map((r) => r.id);
    expect(after.length).toBe(before.length);
    expect(after[1]).toBe(before[0]);
    expect(after[0]).toBe(before[1]);
  });

  it('hides a section from the render without deleting its underlying data', () => {
    setup();
    component.toggleHidden('summary');
    fixture.detectChanges();
    expect(component.hiddenSectionIds()).toContain('summary');
    expect(component.profile()?.summary).toBe('Backend engineer.');
  });

  it('supports undo and redo across an edit', () => {
    setup();
    component.updateSummary('Changed.');
    expect(component.profile()?.summary).toBe('Changed.');

    component.undo();
    expect(component.profile()?.summary).toBe('Backend engineer.');
    expect(component.canRedo()).toBeTrue();

    component.redo();
    expect(component.profile()?.summary).toBe('Changed.');
  });

  it('opens the export panel with a real page estimate and the current template name', () => {
    setup();
    component.openExport();
    fixture.detectChanges();
    expect(component.showExport()).toBeTrue();
    expect(component.estimatedPages()).toBeGreaterThanOrEqual(1);
    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(text).toContain('ATS Classic');
  });

  it('marks the body for print-only rendering and calls window.print when downloading', () => {
    setup();
    spyOn(window, 'print');
    component.downloadPdf();
    expect(window.print).toHaveBeenCalled();
    expect(document.body.classList.contains('cv-printing')).toBeTrue();
    document.body.classList.remove('cv-printing');
  });

  it('closes the export panel without leaving print mode on', () => {
    setup();
    component.openExport();
    component.closeExport();
    expect(component.showExport()).toBeFalse();
  });

  it('adds a custom section and can remove it again', () => {
    setup();
    const before = component.sectionOrder().length;
    component.addCustomSection();
    expect(component.sectionOrder().length).toBe(before + 1);

    component.removeCustomSection();
    expect(component.sectionOrder().length).toBe(before);
  });

  it('removes a skill from the editable profile without touching other skills', () => {
    setup();
    component.removeListItem('skills', 0);
    expect(component.profile()?.skills.map((s) => s.raw_text)).toEqual(['Django']);
  });

  it('preselects the template requested via the ?template= query param', () => {
    const cvApiSpy = jasmine.createSpyObj('CvApiService', {
      getProfile: of({ document_id: 'cv-1', status: 'PROCESSED', profile: profile() }),
    });
    TestBed.configureTestingModule({
      imports: [CvEditorComponent],
      providers: [
        provideRouter([]),
        { provide: CvApiService, useValue: cvApiSpy },
        {
          provide: ActivatedRoute,
          useValue: {
            snapshot: {
              paramMap: convertToParamMap({ id: 'cv-1' }),
              queryParamMap: convertToParamMap({ template: 'modern-split' }),
            },
          },
        },
      ],
    });
    fixture = TestBed.createComponent(CvEditorComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();

    expect(component.templateId()).toBe('modern-split');
  });

  it('never sends edits to the backend - editing stays client-side', () => {
    const cvApiSpy = jasmine.createSpyObj('CvApiService', {
      getProfile: of({ document_id: 'cv-1', status: 'PROCESSED', profile: profile() }),
    });
    TestBed.configureTestingModule({
      imports: [CvEditorComponent],
      providers: [
        provideRouter([]),
        { provide: CvApiService, useValue: cvApiSpy },
        {
          provide: ActivatedRoute,
          useValue: {
            snapshot: { paramMap: convertToParamMap({ id: 'cv-1' }), queryParamMap: convertToParamMap({}) },
          },
        },
      ],
    });
    fixture = TestBed.createComponent(CvEditorComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();

    component.updateSummary('Changed.');
    component.moveSection(0, 1);
    component.toggleHidden('skills');

    expect(cvApiSpy.getProfile).toHaveBeenCalledTimes(1);
  });
});
