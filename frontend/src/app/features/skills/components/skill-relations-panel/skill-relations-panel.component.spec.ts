import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { APP_CONFIG } from '../../../../core/config/app-config';
import { SkillRelationsPanelComponent } from './skill-relations-panel.component';
import { SkillDetail } from '../../models/skill.model';

describe('SkillRelationsPanelComponent', () => {
  let fixture: ComponentFixture<SkillRelationsPanelComponent>;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [SkillRelationsPanelComponent],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: APP_CONFIG, useValue: { apiBaseUrl: 'http://test/api/v1' } },
      ],
    });
    fixture = TestBed.createComponent(SkillRelationsPanelComponent);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => httpMock.verify());

  function detail(overrides: Partial<SkillDetail> = {}): SkillDetail {
    return {
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
      ...overrides,
    };
  }

  it('shows a loading state before the request resolves', () => {
    fixture.componentInstance.canonicalName = 'Django';
    fixture.detectChanges();

    expect((fixture.nativeElement as HTMLElement).textContent).toContain('Loading related skills');
    httpMock.expectOne('http://test/api/v1/skills/Django/').flush(detail());
  });

  it('renders the parent as "Part of" once loaded', () => {
    fixture.componentInstance.canonicalName = 'Django';
    fixture.detectChanges();
    httpMock.expectOne('http://test/api/v1/skills/Django/').flush(detail());
    fixture.detectChanges();

    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(text).toContain('Python');
  });

  it('shows an empty message when the skill has no relationships', () => {
    fixture.componentInstance.canonicalName = 'Rust';
    fixture.detectChanges();
    httpMock.expectOne('http://test/api/v1/skills/Rust/').flush(
      detail({ canonical_name: 'Rust', parent: null, ecosystem: null }),
    );
    fixture.detectChanges();

    expect((fixture.nativeElement as HTMLElement).textContent).toContain('No recorded relationships');
  });

  it('shows an error state on request failure without throwing', () => {
    fixture.componentInstance.canonicalName = 'Django';
    fixture.detectChanges();
    httpMock.expectOne('http://test/api/v1/skills/Django/').flush('boom', { status: 500, statusText: 'Server Error' });
    fixture.detectChanges();

    expect((fixture.nativeElement as HTMLElement).textContent).toContain("Couldn't load related skills");
  });

});
