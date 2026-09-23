import { ComponentFixture, TestBed } from '@angular/core/testing';
import { RequirementMatrixComponent } from './requirement-matrix.component';
import { RequirementEvaluation } from '../../models/analysis.model';

function evaluation(overrides: Partial<RequirementEvaluation> = {}): RequirementEvaluation {
  return {
    requirement_type: 'REQUIRED_SKILL',
    priority: 'MANDATORY',
    raw_text: 'Django',
    status: 'MET',
    match_signal: 'EXACT_MATCH',
    match_strength: 'STRONG',
    score: 1,
    confidence: 0.98,
    matched_skill: 'Django',
    explanation: 'Candidate demonstrates Django directly.',
    evidence: [
      {
        text: 'Built REST APIs using Django.',
        page_number: 1,
        section: 'EXPERIENCE',
        confidence: 0.9,
        extraction_method: 'RULE',
        source_type: 'EXPERIENCE',
        source_label: 'Senior Backend Engineer at Acme',
      },
    ],
    ...overrides,
  };
}

describe('RequirementMatrixComponent', () => {
  let fixture: ComponentFixture<RequirementMatrixComponent>;

  function setup(evaluations: RequirementEvaluation[]): void {
    TestBed.configureTestingModule({ imports: [RequirementMatrixComponent] });
    fixture = TestBed.createComponent(RequirementMatrixComponent);
    fixture.componentInstance.evaluations = evaluations;
    fixture.detectChanges();
  }

  it('renders one row per evaluation', () => {
    setup([evaluation(), evaluation({ raw_text: 'PostgreSQL', matched_skill: 'PostgreSQL' })]);
    const rows = (fixture.nativeElement as HTMLElement).querySelectorAll('.requirement-matrix__row');
    expect(rows.length).toBe(2);
  });

  it('hides evidence until the row is expanded', () => {
    setup([evaluation()]);
    expect((fixture.nativeElement as HTMLElement).querySelector('.requirement-matrix__detail')).toBeNull();

    (fixture.nativeElement as HTMLElement).querySelector<HTMLButtonElement>('.requirement-matrix__summary')!.click();
    fixture.detectChanges();

    const detail = (fixture.nativeElement as HTMLElement).querySelector('.requirement-matrix__detail');
    expect(detail).not.toBeNull();
    expect(detail?.textContent).toContain('Built REST APIs using Django.');
  });

  it('shows a fallback message when a requirement has no evidence', () => {
    setup([evaluation({ evidence: [], match_signal: 'NO_EVIDENCE', explanation: 'No evidence found.' })]);
    (fixture.nativeElement as HTMLElement).querySelector<HTMLButtonElement>('.requirement-matrix__summary')!.click();
    fixture.detectChanges();

    const detail = (fixture.nativeElement as HTMLElement).querySelector('.requirement-matrix__detail');
    expect(detail?.textContent).toContain('No source text is attached');
  });

  it('collapses an already-expanded row on a second click', () => {
    setup([evaluation()]);
    const button = (fixture.nativeElement as HTMLElement).querySelector<HTMLButtonElement>(
      '.requirement-matrix__summary',
    )!;
    button.click();
    fixture.detectChanges();
    button.click();
    fixture.detectChanges();

    expect((fixture.nativeElement as HTMLElement).querySelector('.requirement-matrix__detail')).toBeNull();
  });

  it('renders the match signal badge for each row', () => {
    setup([evaluation()]);
    expect((fixture.nativeElement as HTMLElement).querySelector('app-match-signal-badge')).not.toBeNull();
  });

  it('shows the requirement as the primary label, not the related skill it matched via', () => {
    setup([
      evaluation({
        raw_text: 'Kubernetes',
        matched_skill: 'Docker',
        match_signal: 'RELATED_MATCH',
        explanation: 'Kubernetes itself is not evidenced. Candidate demonstrates Docker (builds on).',
      }),
    ]);
    const text = (fixture.nativeElement as HTMLElement).querySelector('.requirement-matrix__text')!.textContent ?? '';
    expect(text.trim().startsWith('Kubernetes')).toBeTrue();
    expect(text).toContain('via Docker');
  });
});
