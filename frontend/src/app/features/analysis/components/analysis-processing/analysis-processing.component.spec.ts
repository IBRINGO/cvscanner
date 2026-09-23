import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { AnalysisProcessingComponent } from './analysis-processing.component';

describe('AnalysisProcessingComponent', () => {
  let fixture: ComponentFixture<AnalysisProcessingComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({ imports: [AnalysisProcessingComponent] });
    fixture = TestBed.createComponent(AnalysisProcessingComponent);
  });

  it('renders every illustrative stage label', () => {
    fixture.detectChanges();
    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(text).toContain('Reading requirements');
    expect(text).toContain('Building analysis');
  });

  it('never renders a numeric percentage', () => {
    fixture.detectChanges();
    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(text).not.toMatch(/%/);
  });

  it('advances the active stage over time', fakeAsync(() => {
    fixture.detectChanges();
    const firstActive = (fixture.nativeElement as HTMLElement).querySelector('[data-active="true"]')?.textContent;

    tick(1400);
    fixture.detectChanges();
    const secondActive = (fixture.nativeElement as HTMLElement).querySelector('[data-active="true"]')?.textContent;

    expect(secondActive).not.toBe(firstActive);
    fixture.destroy();
  }));

  it('stops advancing after the component is destroyed', fakeAsync(() => {
    fixture.detectChanges();
    fixture.destroy();
    tick(5000); // must not throw or leave a dangling timer
  }));
});
