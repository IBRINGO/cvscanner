import { ComponentFixture, TestBed } from '@angular/core/testing';
import { CandidateProfile } from '../../models/candidate-profile.model';
import { CandidateProfileViewComponent } from './candidate-profile-view.component';

describe('CandidateProfileViewComponent', () => {
  let fixture: ComponentFixture<CandidateProfileViewComponent>;

  function setup(profile: CandidateProfile): void {
    TestBed.configureTestingModule({ imports: [CandidateProfileViewComponent] });
    fixture = TestBed.createComponent(CandidateProfileViewComponent);
    fixture.componentInstance.profile = profile;
    fixture.detectChanges();
  }

  const baseProfile: CandidateProfile = {
    full_name: 'Jordan Rivera',
    email: 'jordan@example.com',
    phone: '+1 415 555 0199',
    location: 'San Francisco, CA',
    links: [],
    summary: 'A short bio.',
    experiences: [
      {
        title: 'Engineer',
        company: 'Acme',
        start_date_raw: '2020',
        end_date_raw: 'Present',
        description: 'Did engineering work.',
        achievements: ['Shipped a thing'],
        technologies: ['Python'],
        seniority: 'MID',
        evidence: {
          page_number: 1,
          section: 'EXPERIENCE',
          text: 'Engineer, Acme',
          confidence: 0.9,
          extraction_method: 'RULE',
        },
      },
    ],
    education: [],
    projects: [],
    certifications: [],
    languages: [
      { name: 'English', proficiency: 'Native', canonical_name: 'English', proficiency_normalized: 'NATIVE' },
    ],
    skills: [
      { raw_text: 'Python', skill: { canonical_name: 'Python', category: 'PROGRAMMING_LANGUAGE' }, evidence: null },
      { raw_text: 'SomeInternalTool', skill: null, evidence: null },
    ],
  };

  it('renders identity and contact information', () => {
    setup(baseProfile);
    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(text).toContain('Jordan Rivera');
    expect(text).toContain('jordan@example.com');
    expect(text).toContain('San Francisco, CA');
  });

  it('renders experience entries with technologies', () => {
    setup(baseProfile);
    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(text).toContain('Engineer');
    expect(text).toContain('Acme');
    expect(text).toContain('Python');
  });

  it('groups skills by category with a human-readable label', () => {
    setup(baseProfile);
    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(text).toContain('Programming Language');
    expect(text).not.toContain('PROGRAMMING_LANGUAGE');
  });

  it('renders an unmatched skill under Uncategorized without dropping it', () => {
    setup(baseProfile);
    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(text).toContain('Uncategorized');
    expect(text).toContain('SomeInternalTool');
  });

  it('does not render a summary section when summary is null', () => {
    setup({ ...baseProfile, summary: null });
    const headings = Array.from((fixture.nativeElement as HTMLElement).querySelectorAll('h2')).map(
      (el) => el.textContent,
    );
    expect(headings).not.toContain('Summary');
  });
});
