import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute, convertToParamMap, provideRouter } from '@angular/router';
import { of } from 'rxjs';
import { AnalysisApiService } from '../../../analysis/services/analysis-api.service';
import { CvApiService } from '../../../cvs/services/cv-api.service';
import { JobApiService } from '../../../jobs/services/job-api.service';
import { TailoringApiService } from '../../../tailoring/services/tailoring-api.service';
import { Recommendation } from '../../models/recommendation.model';
import { RecommendationApiService } from '../../services/recommendation-api.service';
import { RecommendationsPageComponent } from './recommendations-page.component';

function recommendation(overrides: Partial<Recommendation> = {}): Recommendation {
  return {
    id: 'rec-1',
    type: 'RESPONSIBILITY_ALIGNMENT',
    priority: 'MEDIUM',
    confidence: 'MEDIUM',
    safety: 'SAFE_TO_REPHRASE',
    impact: 'MEDIUM_IMPACT',
    title: 'Make existing experience match: REST APIs',
    summary: '...',
    reason: '...',
    suggested_action: '...',
    related_requirement: 1,
    supporting_evidence: [],
    current_state: null,
    target_state: null,
    safe_to_tailor: true,
    created_at: '2026-01-01T00:00:00Z',
    ...overrides,
  };
}

describe('RecommendationsPageComponent', () => {
  let fixture: ComponentFixture<RecommendationsPageComponent>;
  let recommendationApiSpy: jasmine.SpyObj<RecommendationApiService>;
  let tailoringApiSpy: jasmine.SpyObj<TailoringApiService>;

  function setup(recommendations: Recommendation[]): void {
    recommendationApiSpy = jasmine.createSpyObj('RecommendationApiService', ['getForAnalysis']);
    tailoringApiSpy = jasmine.createSpyObj('TailoringApiService', ['create']);
    const analysisApiSpy = jasmine.createSpyObj('AnalysisApiService', ['getAnalysis']);
    const cvApiSpy = jasmine.createSpyObj('CvApiService', ['getProfile']);
    const jobApiSpy = jasmine.createSpyObj('JobApiService', ['getProfile']);

    recommendationApiSpy.getForAnalysis.and.returnValue(of(recommendations));
    analysisApiSpy.getAnalysis.and.returnValue(
      of({ candidate_document_id: 'cv-1', job_document_id: 'job-1' } as never),
    );
    cvApiSpy.getProfile.and.returnValue(of({ profile: { full_name: 'Jordan Rivera' } } as never));
    jobApiSpy.getProfile.and.returnValue(of({ profile: { title: 'Senior Backend Engineer' } } as never));

    TestBed.configureTestingModule({
      imports: [RecommendationsPageComponent],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([]),
        { provide: RecommendationApiService, useValue: recommendationApiSpy },
        { provide: TailoringApiService, useValue: tailoringApiSpy },
        { provide: AnalysisApiService, useValue: analysisApiSpy },
        { provide: CvApiService, useValue: cvApiSpy },
        { provide: JobApiService, useValue: jobApiSpy },
        {
          provide: ActivatedRoute,
          useValue: { snapshot: { paramMap: convertToParamMap({ id: 'analysis-1' }) } },
        },
      ],
    });
    fixture = TestBed.createComponent(RecommendationsPageComponent);
    fixture.detectChanges();
  }

  it('shows an empty state when there are no recommendations', () => {
    setup([]);
    expect((fixture.nativeElement as HTMLElement).textContent).toContain('No recommendations');
  });

  it('shows the recommendation count and high-priority count', () => {
    setup([recommendation({ priority: 'CRITICAL' }), recommendation({ id: 'rec-2', priority: 'LOW' })]);
    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(text).toContain('2 recommendations');
    expect(text).toContain('1 high priority');
  });

  it('only shows the tailoring section when a safe recommendation exists', () => {
    setup([recommendation({ safe_to_tailor: false, safety: 'NOT_SAFE_TO_AUTOMATE' })]);
    expect((fixture.nativeElement as HTMLElement).textContent).not.toContain('Create a tailored CV');
  });

  it('shows the tailoring section when a safe recommendation exists', () => {
    setup([recommendation({ safe_to_tailor: true })]);
    expect((fixture.nativeElement as HTMLElement).textContent).toContain('Create a tailored CV');
  });

  it('disables the tailor button until a recommendation is selected', () => {
    setup([recommendation({ safe_to_tailor: true })]);
    const button = (fixture.nativeElement as HTMLElement).querySelector<HTMLButtonElement>(
      '.recommendations-page__submit',
    )!;
    expect(button.disabled).toBeTrue();
  });

  it('creates a tailoring plan and navigates on success', () => {
    setup([recommendation({ safe_to_tailor: true })]);
    tailoringApiSpy.create.and.returnValue(of({ id: 'plan-1' }) as never);

    fixture.componentInstance.onSelectionChange(['rec-1']);
    fixture.componentInstance.createTailoringPlan();

    expect(tailoringApiSpy.create).toHaveBeenCalledWith('analysis-1', 'CONSERVATIVE', ['rec-1']);
  });
});
