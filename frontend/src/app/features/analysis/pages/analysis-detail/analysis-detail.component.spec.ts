import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed, discardPeriodicTasks, fakeAsync, tick } from '@angular/core/testing';
import { ActivatedRoute, convertToParamMap, provideRouter } from '@angular/router';
import { of } from 'rxjs';
import { CvApiService } from '../../../cvs/services/cv-api.service';
import { JobApiService } from '../../../jobs/services/job-api.service';
import { AnalysisDetail, AnalysisStatusResponse, AnalysisSummary } from '../../models/analysis.model';
import { AnalysisApiService } from '../../services/analysis-api.service';
import { AnalysisDetailComponent } from './analysis-detail.component';

describe('AnalysisDetailComponent', () => {
  let fixture: ComponentFixture<AnalysisDetailComponent>;
  let analysisApiSpy: jasmine.SpyObj<AnalysisApiService>;
  let cvApiSpy: jasmine.SpyObj<CvApiService>;
  let jobApiSpy: jasmine.SpyObj<JobApiService>;

  function summary(overrides: Partial<AnalysisSummary> = {}): AnalysisSummary {
    return {
      id: 'analysis-1',
      candidate_document_id: 'cv-1',
      job_document_id: 'job-1',
      status: 'PENDING',
      engine_version: '1.0.0',
      overall_score: null,
      created_at: '',
      completed_at: null,
      ...overrides,
    };
  }

  function detail(overrides: Partial<AnalysisDetail> = {}): AnalysisDetail {
    return {
      ...summary({ status: 'COMPLETED', overall_score: 0.72 }),
      score_breakdown: {
        overall: 0.72,
        skills: 0.8,
        experience: 0.6,
        seniority: 1,
        education: 1,
        certifications: 0,
        languages: 0,
        responsibilities: 0.5,
        domain: 1,
        mandatory_gap_penalty: 0,
        dimensions: [{ name: 'skills', score: 0.8, weight: 0.3, evaluation_count: 1 }],
      },
      requirement_summary: { total: 1, met: 1, partially_met: 0, not_met: 0, unknown: 0 },
      requirement_evaluations: [
        {
          requirement_type: 'REQUIRED_SKILL',
          priority: 'MANDATORY',
          raw_text: 'Django',
          status: 'MET',
          match_signal: 'EXACT_MATCH',
          match_strength: 'STRONG',
          score: 1,
          confidence: 0.98,
          matched_skill: 'Django',
          explanation: 'Candidate demonstrates Django directly.',
          evidence: [],
        },
      ],
      gaps: [],
      error_message: null,
      ...overrides,
    };
  }

  function pendingDetail(overrides: Partial<AnalysisDetail> = {}): AnalysisDetail {
    return {
      ...summary(),
      score_breakdown: null,
      requirement_summary: { total: 0, met: 0, partially_met: 0, not_met: 0, unknown: 0 },
      requirement_evaluations: [],
      gaps: [],
      error_message: null,
      ...overrides,
    };
  }

  function setup(): void {
    // Force the score gauge's reduced-motion path so its rendered value
    // is available synchronously instead of mid-way through a rAF
    // animation.
    spyOn(window, 'matchMedia').and.returnValue({ matches: true } as MediaQueryList);
    analysisApiSpy = jasmine.createSpyObj('AnalysisApiService', ['getAnalysis', 'getAnalysisStatus']);
    cvApiSpy = jasmine.createSpyObj('CvApiService', ['getProfile']);
    jobApiSpy = jasmine.createSpyObj('JobApiService', ['getProfile']);
    cvApiSpy.getProfile.and.returnValue(
      of({ document_id: 'cv-1', status: 'PROCESSED', profile: { full_name: 'Jordan Rivera' } as never }),
    );
    jobApiSpy.getProfile.and.returnValue(
      of({
        document_id: 'job-1',
        status: 'PROCESSED',
        profile: { title: 'Senior Backend Engineer', company: 'Acme' } as never,
      }),
    );

    TestBed.configureTestingModule({
      imports: [AnalysisDetailComponent],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([]),
        { provide: AnalysisApiService, useValue: analysisApiSpy },
        { provide: CvApiService, useValue: cvApiSpy },
        { provide: JobApiService, useValue: jobApiSpy },
        {
          provide: ActivatedRoute,
          useValue: { snapshot: { paramMap: convertToParamMap({ id: 'analysis-1' }) } },
        },
      ],
    });

    fixture = TestBed.createComponent(AnalysisDetailComponent);
  }

  it(
    'shows the processing state while the analysis is not yet done',
    fakeAsync(() => {
      setup();
      analysisApiSpy.getAnalysis.and.returnValue(of(pendingDetail()));
      analysisApiSpy.getAnalysisStatus.and.returnValue(
        of({ id: 'analysis-1', status: 'PROCESSING', error: null, completed_at: null } as AnalysisStatusResponse),
      );

      fixture.detectChanges();
      tick();
      fixture.detectChanges();

      const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
      expect(text).toContain('Reading requirements');
      discardPeriodicTasks();
    }),
  );

  it(
    'shows candidate and job context once profiles resolve',
    fakeAsync(() => {
      setup();
      analysisApiSpy.getAnalysis.and.returnValue(of(pendingDetail()));
      analysisApiSpy.getAnalysisStatus.and.returnValue(
        of({ id: 'analysis-1', status: 'PROCESSING', error: null, completed_at: null } as AnalysisStatusResponse),
      );

      fixture.detectChanges();
      tick();
      fixture.detectChanges();

      const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
      expect(text).toContain('Jordan Rivera');
      expect(text).toContain('Senior Backend Engineer');
      discardPeriodicTasks();
    }),
  );

  it(
    'renders the full workspace once the analysis completes',
    fakeAsync(() => {
      setup();
      analysisApiSpy.getAnalysis.and.returnValues(of(pendingDetail()), of(detail()));
      analysisApiSpy.getAnalysisStatus.and.returnValue(
        of({ id: 'analysis-1', status: 'COMPLETED', error: null, completed_at: '2026-01-01' } as AnalysisStatusResponse),
      );

      fixture.detectChanges();
      tick();
      fixture.detectChanges();

      const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
      expect(text).toContain('72');
      expect(text).toContain('Django');
    }),
  );

  it(
    'shows a human-readable error state on failure, not a raw error object',
    fakeAsync(() => {
      setup();
      analysisApiSpy.getAnalysis.and.returnValue(of(pendingDetail()));
      analysisApiSpy.getAnalysisStatus.and.returnValue(
        of({
          id: 'analysis-1',
          status: 'FAILED',
          error: 'An unexpected error occurred while running the analysis.',
          completed_at: '2026-01-01',
        } as AnalysisStatusResponse),
      );

      fixture.detectChanges();
      tick();
      fixture.detectChanges();

      const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
      expect(text).toContain('This analysis could not be completed');
      expect(text).toContain('An unexpected error occurred while running the analysis.');
    }),
  );

  it(
    'never renders recommendation content or a candidate ranking - only the journey nav may name that future stage',
    fakeAsync(() => {
      setup();
      analysisApiSpy.getAnalysis.and.returnValues(of(pendingDetail()), of(detail()));
      analysisApiSpy.getAnalysisStatus.and.returnValue(
        of({ id: 'analysis-1', status: 'COMPLETED', error: null, completed_at: '2026-01-01' } as AnalysisStatusResponse),
      );

      fixture.detectChanges();
      tick();
      fixture.detectChanges();

      const root = fixture.nativeElement as HTMLElement;
      expect(root.querySelector('app-recommendation-list')).toBeNull();
      expect(root.querySelector('app-recommendation-card')).toBeNull();

      root.querySelector('app-application-progress')?.remove();
      const text = root.textContent?.toLowerCase() ?? '';
      expect(text).not.toContain('recommend');
      expect(text).not.toContain('ranking');
    }),
  );
});
