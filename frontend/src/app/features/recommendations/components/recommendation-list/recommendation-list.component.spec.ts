import { ComponentFixture, TestBed } from '@angular/core/testing';
import { Recommendation } from '../../models/recommendation.model';
import { RecommendationListComponent } from './recommendation-list.component';

function recommendation(overrides: Partial<Recommendation> = {}): Recommendation {
  return {
    id: 'rec-1',
    type: 'MISSING_REQUIREMENT',
    priority: 'CRITICAL',
    confidence: 'HIGH',
    safety: 'NOT_SAFE_TO_AUTOMATE',
    impact: 'HIGH_IMPACT',
    title: 'Missing skill: Kubernetes',
    summary: 'No evidence of Kubernetes.',
    reason: 'No evidence of Kubernetes.',
    suggested_action: 'This cannot be added automatically.',
    related_requirement: 3,
    supporting_evidence: [],
    current_state: null,
    target_state: 'Kubernetes',
    safe_to_tailor: false,
    created_at: '2026-01-01T00:00:00Z',
    ...overrides,
  };
}

describe('RecommendationListComponent', () => {
  let fixture: ComponentFixture<RecommendationListComponent>;

  function setup(recommendations: Recommendation[]): void {
    TestBed.configureTestingModule({ imports: [RecommendationListComponent] });
    fixture = TestBed.createComponent(RecommendationListComponent);
    fixture.componentInstance.recommendations = recommendations;
    fixture.detectChanges();
  }

  it('groups recommendations by priority with a heading per group', () => {
    setup([recommendation({ priority: 'CRITICAL' }), recommendation({ id: 'rec-2', priority: 'LOW' })]);
    const headings = (fixture.nativeElement as HTMLElement).querySelectorAll('.priority-group__heading');
    expect(headings.length).toBe(2);
  });

  it('does not render a selection checkbox for a not-safe recommendation', () => {
    setup([recommendation({ safe_to_tailor: false })]);
    expect((fixture.nativeElement as HTMLElement).querySelector('.recommendation-list__checkbox')).toBeNull();
  });

  it('renders a selection checkbox for a safe-to-tailor recommendation', () => {
    setup([recommendation({ safe_to_tailor: true, safety: 'SAFE_TO_REPHRASE' })]);
    expect((fixture.nativeElement as HTMLElement).querySelector('.recommendation-list__checkbox')).not.toBeNull();
  });

  it('emits the selection when a safe recommendation is checked', () => {
    setup([recommendation({ safe_to_tailor: true, safety: 'SAFE_TO_REPHRASE' })]);
    const emitted: string[][] = [];
    fixture.componentInstance.selectionChange.subscribe((ids) => emitted.push(ids));

    const checkbox = (fixture.nativeElement as HTMLElement).querySelector<HTMLInputElement>(
      '.recommendation-list__checkbox',
    )!;
    checkbox.checked = true;
    checkbox.dispatchEvent(new Event('change'));

    expect(emitted[0]).toEqual(['rec-1']);
  });

  it('expands a row to show its reason and suggested action', () => {
    setup([recommendation()]);
    (fixture.nativeElement as HTMLElement).querySelector<HTMLButtonElement>('.recommendation-list__toggle')!.click();
    fixture.detectChanges();

    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(text).toContain('This cannot be added automatically.');
  });

  it('shows supporting evidence when present', () => {
    setup([
      recommendation({
        supporting_evidence: [
          {
            text: 'Docker',
            page_number: 1,
            section: 'SKILLS',
            confidence: 0.9,
            extraction_method: 'RULE',
            source_type: 'SKILL_SECTION',
            source_label: null,
          },
        ],
      }),
    ]);
    (fixture.nativeElement as HTMLElement).querySelector<HTMLButtonElement>('.recommendation-list__toggle')!.click();
    fixture.detectChanges();

    expect((fixture.nativeElement as HTMLElement).textContent).toContain('Docker');
  });
});
