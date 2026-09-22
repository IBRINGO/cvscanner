import { ComponentFixture, TestBed } from '@angular/core/testing';
import { JobProfile } from '../../models/job-profile.model';
import { JobProfileViewComponent } from './job-profile-view.component';

describe('JobProfileViewComponent', () => {
  let fixture: ComponentFixture<JobProfileViewComponent>;

  const profile: JobProfile = {
    title: 'Senior Backend Engineer',
    company: 'Meridian Analytics',
    location: 'Remote',
    employment_type: 'Full-time',
    seniority: 'Senior',
    seniority_normalized: 'SENIOR',
    summary: 'We are hiring.',
    responsibilities: ['Build APIs'],
    requirements: [
      {
        requirement_type: 'REQUIRED_SKILL',
        importance: 'REQUIRED',
        raw_text: 'Python',
        skill: { canonical_name: 'Python', category: 'PROGRAMMING_LANGUAGE' },
        minimum_years: null,
        normalized_value: null,
        evidence: null,
      },
      {
        requirement_type: 'PREFERRED_SKILL',
        importance: 'PREFERRED',
        raw_text: 'Docker',
        skill: { canonical_name: 'Docker', category: 'DEVOPS' },
        minimum_years: null,
        normalized_value: null,
        evidence: null,
      },
    ],
  };

  beforeEach(() => {
    TestBed.configureTestingModule({ imports: [JobProfileViewComponent] });
    fixture = TestBed.createComponent(JobProfileViewComponent);
    fixture.componentInstance.profile = profile;
    fixture.detectChanges();
  });

  it('renders the title, company, and location', () => {
    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(text).toContain('Senior Backend Engineer');
    expect(text).toContain('Meridian Analytics');
    expect(text).toContain('Remote');
  });

  it('separates required and preferred requirements under distinct headings', () => {
    const headings = Array.from((fixture.nativeElement as HTMLElement).querySelectorAll('h2')).map(
      (el) => el.textContent,
    );
    expect(headings).toContain('Required');
    expect(headings).toContain('Preferred');
  });

  it('places Python under Required and Docker under Preferred', () => {
    const html = fixture.nativeElement as HTMLElement;
    const requiredSection = Array.from(html.querySelectorAll('section')).find((s) =>
      s.textContent?.includes('Required'),
    );
    const preferredSection = Array.from(html.querySelectorAll('section')).find((s) =>
      s.textContent?.includes('Preferred'),
    );
    expect(requiredSection?.textContent).toContain('Python');
    expect(preferredSection?.textContent).toContain('Docker');
  });

  it('never renders a match-score or compatibility indicator', () => {
    const text = (fixture.nativeElement as HTMLElement).textContent?.toLowerCase() ?? '';
    expect(text).not.toContain('match');
    expect(text).not.toContain('compatib');
  });
});
