import { ComponentFixture, TestBed } from '@angular/core/testing';
import { CandidateProfile } from '../../../cvs/models/candidate-profile.model';
import { DEFAULT_SECTION_ORDER } from '../../../cvs/models/cv-document.model';
import { findTemplate } from '../../models/template-definition.model';
import { CvDocumentRendererComponent, PERSONAL_INFO_ID } from './cv-document-renderer.component';

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
    skills: [{ raw_text: 'Python', skill: null, evidence: null }],
    ...overrides,
  };
}

describe('CvDocumentRendererComponent', () => {
  let fixture: ComponentFixture<CvDocumentRendererComponent>;

  function setup(input: Partial<CvDocumentRendererComponent> = {}): void {
    TestBed.configureTestingModule({ imports: [CvDocumentRendererComponent] });
    fixture = TestBed.createComponent(CvDocumentRendererComponent);
    fixture.componentInstance.profile = input.profile ?? profile();
    fixture.componentInstance.sectionOrder = input.sectionOrder ?? DEFAULT_SECTION_ORDER;
    fixture.componentInstance.hiddenSectionIds = input.hiddenSectionIds ?? [];
    fixture.componentInstance.template = input.template ?? findTemplate('ats-classic');
    fixture.detectChanges();
  }

  it('renders the real candidate name and summary, never a placeholder', () => {
    setup();
    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(text).toContain('Jordan Rivera');
    expect(text).toContain('Built the platform.');
  });

  it('hides a section the caller marked hidden, without dropping the underlying data', () => {
    setup({ hiddenSectionIds: ['skills'] });
    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(text).not.toContain('Python');
    // The profile itself is untouched - only the rendered view omits it.
    expect(fixture.componentInstance.profile.skills.length).toBe(1);
  });

  it('places sidebar-kind sections (skills) in the sidebar for a 2-column template', () => {
    setup({ template: findTemplate('modern-split') });
    const el = fixture.nativeElement as HTMLElement;
    const sidebar = el.querySelector('.cv-page__sidebar');
    expect(sidebar?.textContent).toContain('Python');
  });

  it('renders sections in a single flat column for a 1-column template', () => {
    setup({ template: findTemplate('ats-classic') });
    const el = fixture.nativeElement as HTMLElement;
    expect(el.querySelector('.cv-page__sidebar')).toBeNull();
    expect(el.querySelector('.cv-page__body')?.textContent).toContain('Python');
  });

  it('renders a custom section with the exact user-authored title and content', () => {
    setup({
      sectionOrder: [
        ...DEFAULT_SECTION_ORDER,
        { id: 'custom-1', kind: 'custom', title: 'Awards', content: 'Hackathon winner, 2023.' },
      ],
    });
    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(text).toContain('Awards');
    expect(text).toContain('Hackathon winner, 2023.');
  });

  it('switches visual treatment via data-template without changing the rendered data', () => {
    setup({ template: findTemplate('technical') });
    const page = (fixture.nativeElement as HTMLElement).querySelector('.cv-page');
    expect(page?.getAttribute('data-template')).toBe('technical');
    expect(page?.textContent).toContain('Jordan Rivera');
  });

  it('is not clickable/selectable by default (read-only contexts like the gallery)', () => {
    setup();
    const slot = (fixture.nativeElement as HTMLElement).querySelector('.cv-section-slot');
    expect(slot?.getAttribute('data-interactive')).toBe('false');
  });

  it('emits the clicked section id only when interactive', () => {
    setup();
    fixture.componentRef.setInput('interactive', true);
    fixture.detectChanges();

    const emitted: string[] = [];
    fixture.componentInstance.sectionSelected.subscribe((id) => emitted.push(id));

    const slot = (fixture.nativeElement as HTMLElement).querySelector<HTMLElement>('.cv-page__body .cv-section-slot')!;
    slot.click();
    expect(emitted).toEqual(['summary']);
  });

  it('highlights the section matching selectedSectionId only when interactive', () => {
    setup();
    // OnPush + a bare-fixture root won't re-check on a plain field
    // mutation (nothing marks the view dirty) - setInput is the
    // supported way to simulate a real parent-driven @Input change.
    fixture.componentRef.setInput('interactive', true);
    fixture.componentRef.setInput('selectedSectionId', 'summary');
    fixture.detectChanges();

    const slot = (fixture.nativeElement as HTMLElement).querySelector('.cv-page__body .cv-section-slot');
    expect(slot?.getAttribute('data-selected')).toBe('true');
  });

  it('emits the personal-info sentinel id when the masthead is clicked and interactive', () => {
    setup();
    fixture.componentRef.setInput('interactive', true);
    fixture.detectChanges();

    const emitted: string[] = [];
    fixture.componentInstance.sectionSelected.subscribe((id) => emitted.push(id));

    const header = (fixture.nativeElement as HTMLElement).querySelector<HTMLElement>('.cv-page__header')!;
    header.click();
    expect(emitted).toEqual([PERSONAL_INFO_ID]);
  });
});
