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
      renderPdf: of(new Blob(['%PDF-1.4'], { type: 'application/pdf' })),
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

  it('downloads a server-rendered PDF instead of using the browser print dialog', () => {
    setup();
    component.openExport();
    component.downloadPdf();

    expect(cvApiSpy.renderPdf).toHaveBeenCalledWith(
      jasmine.objectContaining({ template_id: component.templateId() }),
    );
    expect(component.downloading()).toBeFalse();
    expect(component.showExport()).toBeFalse();
  });

  it('surfaces an error and keeps the export panel open if the PDF render fails', () => {
    setup();
    cvApiSpy.renderPdf.and.returnValue(new Observable((subscriber) => subscriber.error(new Error('render failed'))));
    component.openExport();
    component.downloadPdf();

    expect(component.downloadError()).toContain('Could not generate the PDF');
    expect(component.showExport()).toBeTrue();
  });

  it('closes the export panel without leaving print mode on', () => {
    setup();
    component.openExport();
    component.closeExport();
    expect(component.showExport()).toBeFalse();
  });

  it('opens a client-side preview (from the rail, independent of the export dialog) without calling the backend or opening a browser tab', () => {
    setup();
    const openSpy = spyOn(window, 'open');
    component.openPreview();

    expect(component.showPreview()).toBeTrue();
    expect(component.showExport()).toBeFalse();
    expect(cvApiSpy.renderPdf).not.toHaveBeenCalled();
    expect(openSpy).not.toHaveBeenCalled();

    component.closePreview();
    expect(component.showPreview()).toBeFalse();
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

  it('opens and closes the sections dropdown, and auto-closes on select or hide', () => {
    setup();
    expect(component.sectionsMenuOpen()).toBeFalse();

    component.toggleSectionsMenu();
    expect(component.sectionsMenuOpen()).toBeTrue();

    component.selectSectionAndClose('experience');
    expect(component.selectedSectionId()).toBe('experience');
    expect(component.sectionsMenuOpen()).toBeFalse();

    component.toggleSectionsMenu();
    component.toggleHiddenAndClose('skills');
    expect(component.hiddenSectionIds()).toContain('skills');
    expect(component.sectionsMenuOpen()).toBeFalse();
  });

  it('adds an experience/education entry with editable start and end dates', () => {
    setup();
    component.updateExperience(0, 'start_date_raw', '2018');
    component.updateExperience(0, 'end_date_raw', '2021');
    expect(component.profile()?.experiences[0].start_date_raw).toBe('2018');
    expect(component.profile()?.experiences[0].end_date_raw).toBe('2021');

    component.addEducation();
    component.updateEducation(0, 'start_date_raw', '2013');
    component.updateEducation(0, 'end_date_raw', '2017');
    expect(component.profile()?.education[0].start_date_raw).toBe('2013');
    expect(component.profile()?.education[0].end_date_raw).toBe('2017');
  });

  it('assigns a custom category to a skill, and clears it back to uncategorized', () => {
    setup();
    component.updateSkillCategory(0, 'Backend & Frameworks');
    expect(component.profile()?.skills[0].skill).toEqual({
      canonical_name: 'Python',
      category: 'Backend & Frameworks',
    });

    component.updateSkillCategory(0, '   ');
    expect(component.profile()?.skills[0].skill).toBeNull();
  });

  it('reorders experience entries by relevance without losing or duplicating any of them', () => {
    setup({
      cvProfile: profile({
        experiences: [
          { title: 'Role A', company: null, start_date_raw: null, end_date_raw: null, description: '', achievements: [], technologies: [], seniority: null, evidence: null },
          { title: 'Role B', company: null, start_date_raw: null, end_date_raw: null, description: '', achievements: [], technologies: [], seniority: null, evidence: null },
          { title: 'Role C', company: null, start_date_raw: null, end_date_raw: null, description: '', achievements: [], technologies: [], seniority: null, evidence: null },
        ],
      }),
    });

    component.onExperienceDrop({ previousIndex: 2, currentIndex: 0 } as CdkDragDrop<CandidateProfile['experiences']>);

    expect(component.profile()?.experiences.map((e) => e.title)).toEqual(['Role C', 'Role A', 'Role B']);
  });

  it('does nothing when an experience drag ends back at the same position', () => {
    setup();
    const before = component.profile()?.experiences.map((e) => e.title);
    component.onExperienceDrop({ previousIndex: 0, currentIndex: 0 } as CdkDragDrop<CandidateProfile['experiences']>);
    expect(component.profile()?.experiences.map((e) => e.title)).toEqual(before);
    expect(component.canUndo()).toBeFalse();
  });

  it('reorders project entries by relevance without losing or duplicating any of them', () => {
    setup({
      cvProfile: profile({
        projects: [
          { name: 'Project A', description: '', technologies: [] },
          { name: 'Project B', description: '', technologies: [] },
        ],
      }),
    });

    component.onProjectDrop({ previousIndex: 0, currentIndex: 1 } as CdkDragDrop<CandidateProfile['projects']>);

    expect(component.profile()?.projects.map((p) => p.name)).toEqual(['Project B', 'Project A']);
  });

  it('edits personal info (name, email, phone, location) and reflects it live', () => {
    setup();
    component.updatePersonalInfo('full_name', 'Alex Rivera');
    component.updatePersonalInfo('email', 'alex@example.com');
    component.updatePersonalInfo('phone', '555-0100');
    component.updatePersonalInfo('location', 'Austin, TX');
    fixture.detectChanges();

    expect(component.profile()).toEqual(
      jasmine.objectContaining({
        full_name: 'Alex Rivera',
        email: 'alex@example.com',
        phone: '555-0100',
        location: 'Austin, TX',
      }),
    );
    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(text).toContain('Alex Rivera');
  });

  it('adds and removes a personal link', () => {
    setup();
    component.addLink('linkedin.com/in/jordan');
    expect(component.profile()?.links).toEqual(['linkedin.com/in/jordan']);

    component.addLink('   ');
    expect(component.profile()?.links.length).toBe(1);

    component.removeLink(0);
    expect(component.profile()?.links).toEqual([]);
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

  it('adds a new skill, certification and language from free text, ignoring blank input', () => {
    setup();
    component.addSkill('  ');
    expect(component.profile()?.skills.length).toBe(2);

    component.addSkill('Kubernetes');
    expect(component.profile()?.skills.length).toBe(3);
    expect(component.profile()?.skills[2].raw_text).toBe('Kubernetes');

    component.addCertification('AWS Certified Developer');
    expect(component.profile()?.certifications.length).toBe(1);
    expect(component.profile()?.certifications[0].name).toBe('AWS Certified Developer');

    component.addLanguage('Spanish');
    expect(component.profile()?.languages.length).toBe(1);
    expect(component.profile()?.languages[0].name).toBe('Spanish');
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

  it('auto-dismisses the tailored-CV banner a few seconds after load', () => {
    jasmine.clock().install();
    try {
      const plan = tailoringPlan();
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

      expect(component.showTailoredBanner()).toBeTrue();
      jasmine.clock().tick(6001);
      expect(component.showTailoredBanner()).toBeFalse();
    } finally {
      jasmine.clock().uninstall();
    }
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
