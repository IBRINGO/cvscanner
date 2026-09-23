import { ComponentFixture, TestBed } from '@angular/core/testing';
import { RequirementEvaluation } from '../../models/analysis.model';
import { StrengthListComponent } from './strength-list.component';

function evaluation(overrides: Partial<RequirementEvaluation> = {}): RequirementEvaluation {
  return {
    requirement_type: 'REQUIRED_SKILL',
    priority: 'MANDATORY',
    raw_text: 'Python',
    status: 'MET',
    match_signal: 'EXACT_MATCH',
    match_strength: 'STRONG',
    score: 1,
    confidence: 0.9,
    matched_skill: null,
    explanation: 'Found directly on the CV.',
    evidence: [],
    ...overrides,
  };
}

describe('StrengthListComponent', () => {
  let fixture: ComponentFixture<StrengthListComponent>;

  function setup(evaluations: RequirementEvaluation[]): void {
    TestBed.configureTestingModule({ imports: [StrengthListComponent] });
    fixture = TestBed.createComponent(StrengthListComponent);
    fixture.componentInstance.evaluations = evaluations;
    fixture.detectChanges();
  }

  it('shows only requirements with status MET, not partial or missing ones', () => {
    setup([
      evaluation({ raw_text: 'Python', status: 'MET' }),
      evaluation({ raw_text: 'AWS', status: 'NOT_MET' }),
      evaluation({ raw_text: 'Docker', status: 'PARTIALLY_MET' }),
    ]);
    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(text).toContain('Python');
    expect(text).not.toContain('AWS');
    expect(text).not.toContain('Docker');
  });

  it('shows an honest empty state when nothing is fully met', () => {
    setup([evaluation({ status: 'NOT_MET' })]);
    expect((fixture.nativeElement as HTMLElement).textContent).toContain('No requirements are fully met yet');
  });
});
