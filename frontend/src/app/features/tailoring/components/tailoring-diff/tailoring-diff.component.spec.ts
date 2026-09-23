import { ComponentFixture, TestBed } from '@angular/core/testing';
import { TailoringChange } from '../../models/tailoring.model';
import { TailoringDiffComponent } from './tailoring-diff.component';

function change(overrides: Partial<TailoringChange> = {}): TailoringChange {
  return {
    fact_id: 'experience:0',
    recommendation_title: 'Make existing experience match: REST APIs',
    original_text: 'Built internal tooling.',
    final_text: 'Built internal tooling using REST APIs.',
    diff: [
      { text: 'Built internal tooling', change_type: 'UNCHANGED' },
      { text: 'using REST APIs', change_type: 'ADDED' },
    ],
    accepted: true,
    rejection_reasons: [],
    ...overrides,
  };
}

describe('TailoringDiffComponent', () => {
  let fixture: ComponentFixture<TailoringDiffComponent>;

  function setup(value: TailoringChange): void {
    TestBed.configureTestingModule({ imports: [TailoringDiffComponent] });
    fixture = TestBed.createComponent(TailoringDiffComponent);
    fixture.componentInstance.change = value;
    fixture.detectChanges();
  }

  it('marks an accepted change as applied', () => {
    setup(change());
    expect((fixture.nativeElement as HTMLElement).textContent).toContain('Applied');
  });

  it('highlights added text distinctly from unchanged text', () => {
    setup(change());
    const added = (fixture.nativeElement as HTMLElement).querySelector("[data-change='ADDED']");
    expect(added?.textContent).toContain('REST APIs');
  });

  it('shows the original text and a rejection reason for a rejected change', () => {
    setup(
      change({
        accepted: false,
        final_text: 'Built internal tooling.',
        rejection_reasons: ['UNSUPPORTED_TECHNOLOGY'],
      }),
    );
    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(text).toContain('Not applied');
    expect(text).toContain('Built internal tooling.');
    expect(text.toLowerCase()).toContain('unsupported technology');
  });

  it('never silently hides a rejected change', () => {
    setup(change({ accepted: false, rejection_reasons: ['DURATION_INFLATION'] }));
    expect((fixture.nativeElement as HTMLElement).textContent?.trim().length).toBeGreaterThan(0);
  });
});
