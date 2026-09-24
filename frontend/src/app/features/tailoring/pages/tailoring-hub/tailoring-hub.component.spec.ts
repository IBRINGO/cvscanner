import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { of } from 'rxjs';
import { TailoringPlanSummary } from '../../models/tailoring.model';
import { TailoringApiService } from '../../services/tailoring-api.service';
import { TailoringHubComponent } from './tailoring-hub.component';

function plan(overrides: Partial<TailoringPlanSummary> = {}): TailoringPlanSummary {
  return {
    id: 'plan-1',
    analysis_id: 'analysis-1',
    mode: 'CONSERVATIVE',
    engine_version: '1.0.0',
    status: 'COMPLETED',
    before_score: 0.72,
    after_score: 0.81,
    created_at: '2026-01-01T00:00:00Z',
    completed_at: '2026-01-01T00:00:00Z',
    ...overrides,
  };
}

describe('TailoringHubComponent', () => {
  let fixture: ComponentFixture<TailoringHubComponent>;
  let tailoringApiSpy: jasmine.SpyObj<TailoringApiService>;

  function setup(plans: TailoringPlanSummary[]): void {
    tailoringApiSpy = jasmine.createSpyObj('TailoringApiService', ['list']);
    tailoringApiSpy.list.and.returnValue(of(plans));

    TestBed.configureTestingModule({
      imports: [TailoringHubComponent],
      providers: [provideRouter([]), { provide: TailoringApiService, useValue: tailoringApiSpy }],
    });
    fixture = TestBed.createComponent(TailoringHubComponent);
    fixture.detectChanges();
  }

  it('shows an empty state pointing to the analysis workspace when there are no plans', () => {
    setup([]);
    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(text).toContain('No tailored CVs yet');
  });

  it('lists past tailoring runs with their status', () => {
    setup([plan({ status: 'COMPLETED' })]);
    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(text).toContain('Completed');
  });

  it('shows the before/after match score for a completed run', () => {
    setup([plan({ status: 'COMPLETED', before_score: 0.72, after_score: 0.81 })]);
    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(text).toContain('72%');
    expect(text).toContain('81%');
  });

  it('does not show a score for a run that has not completed', () => {
    setup([plan({ status: 'GENERATING', before_score: null, after_score: null })]);
    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(text).toContain('Generating');
    expect(text).not.toContain('%');
  });

  it('links each row to that plan detail page', () => {
    setup([plan({ id: 'plan-99' })]);
    const link = (fixture.nativeElement as HTMLElement).querySelector('a.document-index__link')!;
    expect(link.getAttribute('href')).toBe('/tailoring/plan-99');
  });
});
