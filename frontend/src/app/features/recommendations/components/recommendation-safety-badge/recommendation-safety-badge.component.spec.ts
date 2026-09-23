import { ComponentFixture, TestBed } from '@angular/core/testing';
import { RecommendationSafetyBadgeComponent } from './recommendation-safety-badge.component';

describe('RecommendationSafetyBadgeComponent', () => {
  let fixture: ComponentFixture<RecommendationSafetyBadgeComponent>;

  function setup(safety: RecommendationSafetyBadgeComponent['safety']): void {
    TestBed.configureTestingModule({ imports: [RecommendationSafetyBadgeComponent] });
    fixture = TestBed.createComponent(RecommendationSafetyBadgeComponent);
    fixture.componentInstance.safety = safety;
    fixture.detectChanges();
  }

  it('labels a safe-to-rephrase recommendation as safe, not a raw enum value', () => {
    setup('SAFE_TO_REPHRASE');
    expect((fixture.nativeElement as HTMLElement).textContent).toContain('Safe to rephrase');
  });

  it('labels a not-safe recommendation clearly as unsupported, not silently green', () => {
    setup('NOT_SAFE_TO_AUTOMATE');
    const badge = (fixture.nativeElement as HTMLElement).querySelector('.safety-badge');
    expect(badge?.getAttribute('data-tone')).toBe('negative');
  });

  it('never renders the raw enum value as the visible label', () => {
    setup('REQUIRES_CANDIDATE_CONFIRMATION');
    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(text).not.toContain('REQUIRES_CANDIDATE_CONFIRMATION');
  });
});
