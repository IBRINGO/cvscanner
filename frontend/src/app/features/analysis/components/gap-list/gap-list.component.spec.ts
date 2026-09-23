import { ComponentFixture, TestBed } from '@angular/core/testing';
import { GapListComponent } from './gap-list.component';
import { Gap } from '../../models/analysis.model';

function gap(overrides: Partial<Gap> = {}): Gap {
  return {
    requirement_type: 'REQUIRED_SKILL',
    priority: 'MANDATORY',
    raw_text: 'Kubernetes',
    reason: 'No evidence of Kubernetes or a related skill.',
    evidence_status: 'NO_EVIDENCE',
    related_candidate_skills: [],
    confidence: 0.9,
    ...overrides,
  };
}

describe('GapListComponent', () => {
  let fixture: ComponentFixture<GapListComponent>;

  function setup(gaps: Gap[]): void {
    TestBed.configureTestingModule({ imports: [GapListComponent] });
    fixture = TestBed.createComponent(GapListComponent);
    fixture.componentInstance.gaps = gaps;
    fixture.detectChanges();
  }

  it('shows an intentional empty state when there are no gaps', () => {
    setup([]);
    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(text).toContain('No gaps identified');
  });

  it('renders one entry per gap with its reason', () => {
    setup([gap(), gap({ raw_text: 'AWS Certified Solutions Architect' })]);
    const items = (fixture.nativeElement as HTMLElement).querySelectorAll('.gap-list__item');
    expect(items.length).toBe(2);
    expect(items[0].textContent).toContain('No evidence of Kubernetes');
  });

  it('shows related candidate skills when present', () => {
    setup([gap({ related_candidate_skills: ['Docker'] })]);
    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(text).toContain('Docker');
  });

  it('never renders a recommendation or suggested action', () => {
    setup([gap()]);
    const text = (fixture.nativeElement as HTMLElement).textContent?.toLowerCase() ?? '';
    expect(text).not.toContain('recommend');
    expect(text).not.toContain('suggestion');
  });
});
