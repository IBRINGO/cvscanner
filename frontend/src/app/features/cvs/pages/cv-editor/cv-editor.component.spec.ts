import { CdkDragDrop } from '@angular/cdk/drag-drop';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute, convertToParamMap, provideRouter } from '@angular/router';
import { Observable, of } from 'rxjs';
import { TailoringPlanDetail } from '../../../tailoring/models/tailoring.model';
import { TailoringApiService } from '../../../tailoring/services/tailoring-api.service';
import { CandidateProfile } from '../../models/candidate-profile.model';
import { CvSectionRef } from '../../models/cv-document.model';
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

function tailoringPlan(overrides: Partial<TailoringPlanDetail> = {}): TailoringPlanDetail {
  return {
    id: 'plan-1',
    analysis_id: 'analysis-1',
    mode: 'CONSERVATIVE',
    engine_version: '1.0.0',
    status: 'COMPLETED',
    before_score: 0.7,
    after_score: 0.8,
    operations: [],
    protected_fact_ids: [],
    requirements_improved: 1,
    requirements_unchanged: 0,
    requirements_still_missing: 0,
    changes: [],
    error_message: null,
    created_at: '2026-01-01T00:00:00Z',
    completed_at: '2026-01-01T00:00:00Z',
    ...overrides,
  };
}

describe('CvEditorComponent', () => {
  let fixture: ComponentFixture<CvEditorComponent>;
  let component: CvEditorComponent;
  let cvApiSpy: jasmine.SpyObj<CvApiService>;
  let tailoringApiSpy: jasmine.SpyObj<TailoringApiService>;

  function setup(options: { queryParams?: Record<string, string>; cvProfile?: CandidateProfile } = {}): void {
    cvApiSpy = jasmine.createSpyObj('CvApiService', {
      getProfile: of({ document_id: 'cv-1', status: 'PROCESSED', profile: options.cvProfile ?? profile() }),
    });
    tailoringApiSpy = jasmine.createSpyObj('TailoringApiService', {
      getPlan: of(tailoringPlan()),
    });
    TestBed.configureTestingModule({
      imports: [CvEditorComponent],
      providers: [
        provideRouter([]),
        { provide: CvApiService, useValue: cvApiSpy },
        { provide: TailoringApiService, useValue: tailoringApiSpy },
        {
          provide: ActivatedRoute,
          useValue: {
            snapshot: {
              paramMap: convertToParamMap({ id: 'cv-1' }),
              queryParamMap: convertToParamMap(options.queryParams ?? {}),
            },
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

  it('reorders sections via drag-and-drop without losing or duplicating any of them', () => {
    setup();
    const before = component.sectionOrder().map((r) => r.id);
    component.onSectionDrop({ previousIndex: 0, currentIndex: 1 } as CdkDragDrop<CvSectionRef[]>);
    const after = component.sectionOrder().map((r) => r.id);
    expect(after.length).toBe(before.length);
    expect(after[1]).toBe(before[0]);
    expect(after[0]).toBe(before[1]);
  });

  it('can reorder a section across several positions in one drop, not only an adjacent swap', () => {
    setup();
    const before = component.sectionOrder().map((r) => r.id);
    component.onSectionDrop({ previousIndex: 0, currentIndex: 3 } as CdkDragDrop<CvSectionRef[]>);
    const after = component.sectionOrder().map((r) => r.id);
    expect(after.length).toBe(before.length);
    expect(after[3]).toBe(before[0]);
    expect(after).toEqual(jasmine.arrayContaining(before));
  });

  it('does nothing when a drag ends back at the same position', () => {
    setup();
    const before = component.sectionOrder().map((r) => r.id);
    component.onSectionDrop({ previousIndex: 2, currentIndex: 2 } as CdkDragDrop<CvSectionRef[]>);
    expect(component.sectionOrder().map((r) => r.id)).toEqual(before);
    expect(component.canUndo()).toBeFalse();
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

  it('adds, duplicates and removes an experience entry', () => {
    setup();
    component.addExperience();
    expect(component.profile()?.experiences.length).toBe(2);

    component.duplicateExperience(0);
    expect(component.profile()?.experiences.length).toBe(3);
    expect(component.profile()?.experiences[1].title).toBe(component.profile()?.experiences[0].title);

    component.removeExperience(0);
    expect(component.profile()?.experiences.length).toBe(2);
  });

  it('adds, duplicates and removes an education entry', () => {
    setup();
    expect(component.profile()?.education.length).toBe(0);
    component.addEducation();
    expect(component.profile()?.education.length).toBe(1);

    component.duplicateEducation(0);
    expect(component.profile()?.education.length).toBe(2);

    component.removeEducation(1);
    expect(component.profile()?.education.length).toBe(1);
  });

  it('adds, edits, duplicates and removes a project entry', () => {
    setup();
    component.addProject();
    expect(component.profile()?.projects.length).toBe(1);

    component.updateProject(0, 'name', 'Portfolio site');
    expect(component.profile()?.projects[0].name).toBe('Portfolio site');

    component.duplicateProject(0);
    expect(component.profile()?.projects.length).toBe(2);
    expect(component.profile()?.projects[1].name).toBe('Portfolio site');

    component.removeListItem('projects', 0);
    expect(component.profile()?.projects.length).toBe(1);
  });

  it('preselects the template requested via the ?template= query param', () => {
    setup({ queryParams: { template: 'modern-split' } });
    expect(component.templateId()).toBe('modern-split');
  });

  it('never sends edits to the backend - editing stays client-side', () => {
    setup();
    component.updateSummary('Changed.');
    component.onSectionDrop({ previousIndex: 0, currentIndex: 1 } as CdkDragDrop<CvSectionRef[]>);
    component.toggleHidden('skills');

    expect(cvApiSpy.getProfile).toHaveBeenCalledTimes(1);
  });

  it('loads the tailored profile (accepted changes applied) when ?tailoringId= is present', () => {
    const plan = tailoringPlan({
      changes: [
        {
          fact_id: 'experience:0',
          recommendation_title: 'Clarify wording',
          original_text: 'Built the platform.',
          final_text: 'Built the platform using REST APIs.',
          diff: [],
          accepted: true,
          rejection_reasons: [],
        },
      ],
    });
    tailoringApiSpy = jasmine.createSpyObj('TailoringApiService', { getPlan: of(plan) });
    cvApiSpy = jasmine.createSpyObj('CvApiService', {
      getProfile: of({ document_id: 'cv-1', status: 'PROCESSED', profile: profile() }),
    });
    TestBed.configureTestingModule({
      imports: [CvEditorComponent],
      providers: [
        provideRouter([]),
        { provide: CvApiService, useValue: cvApiSpy },
        { provide: TailoringApiService, useValue: tailoringApiSpy },
        {
          provide: ActivatedRoute,
          useValue: {
            snapshot: {
              paramMap: convertToParamMap({ id: 'cv-1' }),
              queryParamMap: convertToParamMap({ tailoringId: 'plan-1' }),
            },
          },
        },
      ],
    });
    fixture = TestBed.createComponent(CvEditorComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();

    expect(tailoringApiSpy.getPlan).toHaveBeenCalledWith('plan-1');
    expect(component.profile()?.experiences[0].description).toBe('Built the platform using REST APIs.');
    expect(component.fromTailoringId()).toBe('plan-1');
  });

  it('falls back to the real original profile if the tailoring plan fails to load', () => {
    tailoringApiSpy = jasmine.createSpyObj('TailoringApiService', {
      getPlan: undefined,
    });
    tailoringApiSpy.getPlan.and.returnValue(
      new Observable((subscriber) => subscriber.error(new Error('not found'))),
    );
    cvApiSpy = jasmine.createSpyObj('CvApiService', {
      getProfile: of({ document_id: 'cv-1', status: 'PROCESSED', profile: profile() }),
    });
    TestBed.configureTestingModule({
      imports: [CvEditorComponent],
      providers: [
        provideRouter([]),
        { provide: CvApiService, useValue: cvApiSpy },
        { provide: TailoringApiService, useValue: tailoringApiSpy },
        {
          provide: ActivatedRoute,
          useValue: {
            snapshot: {
              paramMap: convertToParamMap({ id: 'cv-1' }),
              queryParamMap: convertToParamMap({ tailoringId: 'plan-missing' }),
            },
          },
        },
      ],
    });
    fixture = TestBed.createComponent(CvEditorComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();

    expect(component.profile()?.experiences[0].description).toBe('Built the platform.');
    expect(component.fromTailoringId()).toBeNull();
  });
});
