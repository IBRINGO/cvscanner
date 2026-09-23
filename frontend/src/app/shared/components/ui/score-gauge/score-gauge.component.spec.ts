import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ScoreGaugeComponent } from './score-gauge.component';

describe('ScoreGaugeComponent', () => {
  let fixture: ComponentFixture<ScoreGaugeComponent>;

  function setup(score: number): void {
    fixture = TestBed.createComponent(ScoreGaugeComponent);
    fixture.componentInstance.score = score;
    fixture.componentInstance.ngOnChanges();
    fixture.detectChanges();
  }

  beforeEach(() => {
    TestBed.configureTestingModule({ imports: [ScoreGaugeComponent] });
    // Force the reduced-motion path so the rendered value is available
    // synchronously instead of mid-way through a rAF-driven animation.
    spyOn(window, 'matchMedia').and.returnValue({ matches: true } as MediaQueryList);
  });

  it('renders the exact rounded score, never inflating it', () => {
    setup(0.83);
    const el = fixture.nativeElement as HTMLElement;
    expect(el.querySelector('.gauge__number')?.textContent?.trim()).toBe('83');
  });

  it('clamps out-of-range scores instead of rendering nonsense', () => {
    setup(1.4);
    const el = fixture.nativeElement as HTMLElement;
    expect(el.querySelector('.gauge__number')?.textContent?.trim()).toBe('100');
  });

  it('exposes an accessible label with the real value', () => {
    setup(0.5);
    expect(fixture.componentInstance.ariaLabel()).toContain('50');
  });
});
