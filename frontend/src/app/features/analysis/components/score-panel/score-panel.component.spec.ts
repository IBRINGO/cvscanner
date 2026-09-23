import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ScorePanelComponent } from './score-panel.component';
import { ScoreBreakdown } from '../../models/analysis.model';

function breakdown(overrides: Partial<ScoreBreakdown> = {}): ScoreBreakdown {
  return {
    overall: 0.72,
    skills: 0.8,
    experience: 0.6,
    seniority: 1,
    education: 1,
    certifications: 0,
    languages: 0,
    responsibilities: 0.5,
    domain: 1,
    mandatory_gap_penalty: 0,
    dimensions: [
      { name: 'skills', score: 0.8, weight: 0.3, evaluation_count: 3 },
      { name: 'experience', score: 0.6, weight: 0.2, evaluation_count: 1 },
    ],
    ...overrides,
  };
}

describe('ScorePanelComponent', () => {
  let fixture: ComponentFixture<ScorePanelComponent>;

  function setup(input: Partial<ScorePanelComponent> = {}): void {
    // Force the gauge's reduced-motion path so its rendered value is
    // available synchronously instead of mid-way through a rAF animation.
    spyOn(window, 'matchMedia').and.returnValue({ matches: true } as MediaQueryList);
    TestBed.configureTestingModule({ imports: [ScorePanelComponent] });
    fixture = TestBed.createComponent(ScorePanelComponent);
    fixture.componentInstance.breakdown = input.breakdown ?? breakdown();
    if (input.mandatoryGapCount !== undefined) {
      fixture.componentInstance.mandatoryGapCount = input.mandatoryGapCount;
    }
    fixture.detectChanges();
  }

  it('renders the overall score as a whole-number percentage', () => {
    setup();
    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(text).toContain('72');
  });

  it('renders every dimension as a labelled bar with its own score', () => {
    setup();
    const rows = (fixture.nativeElement as HTMLElement).querySelectorAll('.score-panel__row');
    expect(rows.length).toBe(2);
    expect(rows[0].textContent).toContain('80');
  });

  it('shows a mandatory-gap note only when a penalty was applied', () => {
    setup({ breakdown: breakdown({ mandatory_gap_penalty: 0.15 }), mandatoryGapCount: 1 });
    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(text).toContain('missing mandatory requirement');
  });

  it('does not show a mandatory-gap note when there is no penalty', () => {
    setup({ breakdown: breakdown({ mandatory_gap_penalty: 0 }) });
    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(text).not.toContain('missing mandatory requirement');
  });

  it('renders the score as an animated gauge with the exact real value, not a fabricated one', () => {
    setup({ breakdown: breakdown({ overall: 0.83 }) });
    const el = fixture.nativeElement as HTMLElement;
    expect(el.querySelector('app-score-gauge')).toBeTruthy();
    expect(el.querySelector('.gauge__number')?.textContent?.trim()).toBe('83');
  });
});
