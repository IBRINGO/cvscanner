import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { APP_CONFIG } from '../../../../core/config/app-config';
import { SkillChipComponent } from './skill-chip.component';

describe('SkillChipComponent', () => {
  let fixture: ComponentFixture<SkillChipComponent>;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [SkillChipComponent],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: APP_CONFIG, useValue: { apiBaseUrl: 'http://test/api/v1' } },
      ],
    });
    fixture = TestBed.createComponent(SkillChipComponent);
    httpMock = TestBed.inject(HttpTestingController);
  });

  it('shows the canonical name when the skill matched the taxonomy', () => {
    fixture.componentInstance.rawText = 'js';
    fixture.componentInstance.skill = { canonical_name: 'JavaScript', category: 'PROGRAMMING_LANGUAGE' };
    fixture.detectChanges();

    const button = (fixture.nativeElement as HTMLElement).querySelector('.skill-chip');
    expect(button?.getAttribute('data-matched')).toBe('true');
    expect(button?.textContent).toContain('JavaScript');
  });

  it('marks an unmatched skill as unmatched and shows the raw text', () => {
    fixture.componentInstance.rawText = 'SomeInternalTool';
    fixture.componentInstance.skill = null;
    fixture.detectChanges();

    const button = (fixture.nativeElement as HTMLElement).querySelector('.skill-chip');
    expect(button?.getAttribute('data-matched')).toBe('false');
    expect(button?.textContent).toContain('SomeInternalTool');
  });

  it('shows no related-skills toggle for an unmatched skill', () => {
    fixture.componentInstance.rawText = 'SomeInternalTool';
    fixture.componentInstance.skill = null;
    fixture.detectChanges();

    expect((fixture.nativeElement as HTMLElement).querySelector('.skill-chip__relations-toggle')).toBeNull();
  });

  it('shows a related-skills toggle for a matched skill', () => {
    fixture.componentInstance.rawText = 'Python';
    fixture.componentInstance.skill = { canonical_name: 'Python', category: 'PROGRAMMING_LANGUAGE' };
    fixture.detectChanges();

    expect((fixture.nativeElement as HTMLElement).querySelector('.skill-chip__relations-toggle')).not.toBeNull();
  });

  it('reveals evidence only after being clicked', () => {
    fixture.componentInstance.rawText = 'Python';
    fixture.componentInstance.skill = { canonical_name: 'Python', category: 'PROGRAMMING_LANGUAGE' };
    fixture.componentInstance.evidence = {
      page_number: 2,
      section: 'SKILLS',
      text: 'Python, Django',
      confidence: 0.95,
      extraction_method: 'RULE',
    };
    fixture.detectChanges();

    expect((fixture.nativeElement as HTMLElement).querySelector('app-evidence-note')).toBeNull();

    (fixture.nativeElement as HTMLElement).querySelector<HTMLButtonElement>('.skill-chip')!.click();
    fixture.detectChanges();

    expect((fixture.nativeElement as HTMLElement).querySelector('app-evidence-note')).not.toBeNull();
  });

  it('lazily fetches related skills only when the relations toggle is clicked', () => {
    fixture.componentInstance.rawText = 'Django';
    fixture.componentInstance.skill = { canonical_name: 'Django', category: 'FRAMEWORK' };
    fixture.detectChanges();

    httpMock.expectNone('http://test/api/v1/skills/Django/');

    (fixture.nativeElement as HTMLElement).querySelector<HTMLButtonElement>('.skill-chip__relations-toggle')!.click();
    fixture.detectChanges();

    httpMock.expectOne('http://test/api/v1/skills/Django/').flush({
      canonical_name: 'Django',
      category: 'FRAMEWORK',
      domain: 'SOFTWARE_DEVELOPMENT',
      aliases: [],
      ecosystem: 'Python ecosystem',
      description: null,
      parent: { canonical_name: 'Python', category: 'PROGRAMMING_LANGUAGE', domain: 'SOFTWARE_DEVELOPMENT', description: null },
      children: [],
      ecosystem_siblings: [],
      explicit: [],
    });
    fixture.detectChanges();

    expect((fixture.nativeElement as HTMLElement).querySelector('app-skill-relations-panel')).not.toBeNull();
  });
});
