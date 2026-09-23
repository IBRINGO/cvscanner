import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ApplicationProgressComponent } from './application-progress.component';

describe('ApplicationProgressComponent', () => {
  let fixture: ComponentFixture<ApplicationProgressComponent>;

  function setup(current: string, completed: string[] = []): void {
    fixture = TestBed.createComponent(ApplicationProgressComponent);
    fixture.componentInstance.current = current as never;
    fixture.componentInstance.completed = completed as never;
    fixture.detectChanges();
  }

  beforeEach(() => {
    TestBed.configureTestingModule({ imports: [ApplicationProgressComponent] });
  });

  it('marks the current stage as active', () => {
    setup('analysis', ['cv', 'job']);
    const steps = (fixture.nativeElement as HTMLElement).querySelectorAll('.progress__step');
    expect(steps[2].getAttribute('data-state')).toBe('active');
  });

  it('marks only explicitly completed stages as done, not everything before the active one', () => {
    setup('tailoring', ['cv']);
    const steps = (fixture.nativeElement as HTMLElement).querySelectorAll('.progress__step');
    expect(steps[0].getAttribute('data-state')).toBe('done');
    expect(steps[1].getAttribute('data-state')).toBe('pending');
    expect(steps[2].getAttribute('data-state')).toBe('pending');
  });

  it('renders all six stage labels', () => {
    setup('cv');
    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    for (const label of ['CV', 'Job', 'Analysis', 'Recommendations', 'Tailoring', 'Export']) {
      expect(text).toContain(label);
    }
  });
});
