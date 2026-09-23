import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { of } from 'rxjs';
import { AnalysisSummary } from '../../../analysis/models/analysis.model';
import { AnalysisApiService } from '../../../analysis/services/analysis-api.service';
import { RecommendationsHubComponent } from './recommendations-hub.component';

function analysis(overrides: Partial<AnalysisSummary> = {}): AnalysisSummary {
  return {
    id: 'analysis-1',
    candidate_document_id: 'cv-1',
    job_document_id: 'job-1',
    status: 'COMPLETED',
    engine_version: '1.0.0',
    overall_score: 0.83,
    created_at: '2026-01-01T00:00:00Z',
    completed_at: '2026-01-01T00:00:00Z',
    ...overrides,
  };
}

describe('RecommendationsHubComponent', () => {
  let fixture: ComponentFixture<RecommendationsHubComponent>;
  let analysisApiSpy: jasmine.SpyObj<AnalysisApiService>;

  function setup(analyses: AnalysisSummary[]): void {
    analysisApiSpy = jasmine.createSpyObj('AnalysisApiService', ['list']);
    analysisApiSpy.list.and.returnValue(of(analyses));

    TestBed.configureTestingModule({
      imports: [RecommendationsHubComponent],
      providers: [provideRouter([]), { provide: AnalysisApiService, useValue: analysisApiSpy }],
    });
    fixture = TestBed.createComponent(RecommendationsHubComponent);
    fixture.detectChanges();
  }

  it('shows an empty state when there are no completed analyses', () => {
    setup([]);
    expect((fixture.nativeElement as HTMLElement).textContent).toContain('No completed analyses yet');
  });

  it('lists only completed analyses, not pending ones', () => {
    setup([analysis({ id: 'a', status: 'COMPLETED' }), analysis({ id: 'b', status: 'PENDING' })]);
    const rows = (fixture.nativeElement as HTMLElement).querySelectorAll('.document-index__row');
    expect(rows.length).toBe(1);
  });

  it('links each row to that analysis\'s recommendations page', () => {
    setup([analysis({ id: 'analysis-42' })]);
    const link = (fixture.nativeElement as HTMLElement).querySelector('a.document-index__link')!;
    expect(link.getAttribute('href')).toBe('/analysis/analysis-42/recommendations');
  });
});
