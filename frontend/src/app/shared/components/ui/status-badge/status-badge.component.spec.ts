import { ComponentFixture, TestBed } from '@angular/core/testing';
import { StatusBadgeComponent } from './status-badge.component';

describe('StatusBadgeComponent', () => {
  let fixture: ComponentFixture<StatusBadgeComponent>;

  function setup(status: string) {
    fixture = TestBed.createComponent(StatusBadgeComponent);
    fixture.componentInstance.status = status as never;
    fixture.detectChanges();
  }

  beforeEach(() => {
    TestBed.configureTestingModule({ imports: [StatusBadgeComponent] });
  });

  it('renders a human label for PROCESSED', () => {
    setup('PROCESSED');
    expect((fixture.nativeElement as HTMLElement).textContent).toContain('Ready');
  });

  it('renders a human label for FAILED', () => {
    setup('FAILED');
    expect((fixture.nativeElement as HTMLElement).textContent).toContain('Failed');
  });

  it('sets a data-status attribute matching the raw status for styling', () => {
    setup('PROCESSING');
    const badge = (fixture.nativeElement as HTMLElement).querySelector('.status-badge');
    expect(badge?.getAttribute('data-status')).toBe('PROCESSING');
  });
});
