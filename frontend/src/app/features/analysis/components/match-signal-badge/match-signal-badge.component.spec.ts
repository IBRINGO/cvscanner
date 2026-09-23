import { ComponentFixture, TestBed } from '@angular/core/testing';
import { MatchSignalBadgeComponent } from './match-signal-badge.component';

describe('MatchSignalBadgeComponent', () => {
  let fixture: ComponentFixture<MatchSignalBadgeComponent>;

  function setup(signal: MatchSignalBadgeComponent['signal']): void {
    TestBed.configureTestingModule({ imports: [MatchSignalBadgeComponent] });
    fixture = TestBed.createComponent(MatchSignalBadgeComponent);
    fixture.componentInstance.signal = signal;
    fixture.detectChanges();
  }

  it('shows a positive tone and label for an exact match', () => {
    setup('EXACT_MATCH');
    const badge = (fixture.nativeElement as HTMLElement).querySelector('.match-signal-badge');
    expect(badge?.getAttribute('data-tone')).toBe('positive');
    expect(badge?.textContent).toContain('Exact match');
  });

  it('shows a distinct semantic tone for a semantic match, never positive', () => {
    setup('SEMANTIC_MATCH');
    const badge = (fixture.nativeElement as HTMLElement).querySelector('.match-signal-badge');
    expect(badge?.getAttribute('data-tone')).toBe('semantic');
    expect(badge?.getAttribute('data-tone')).not.toBe('positive');
  });

  it('shows a negative tone for no evidence', () => {
    setup('NO_EVIDENCE');
    const badge = (fixture.nativeElement as HTMLElement).querySelector('.match-signal-badge');
    expect(badge?.getAttribute('data-tone')).toBe('negative');
  });

  it('never uses the same tone for related and exact matches', () => {
    setup('RELATED_MATCH');
    const relatedTone = (fixture.nativeElement as HTMLElement)
      .querySelector('.match-signal-badge')
      ?.getAttribute('data-tone');
    expect(relatedTone).not.toBe('positive');
  });
});
