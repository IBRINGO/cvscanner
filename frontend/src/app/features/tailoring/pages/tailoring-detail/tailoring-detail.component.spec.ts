import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed, discardPeriodicTasks, fakeAsync, tick } from '@angular/core/testing';
import { ActivatedRoute, convertToParamMap, provideRouter } from '@angular/router';
import { of } from 'rxjs';
import { TailoringPlanDetail, TailoringStatusResponse } from '../../models/tailoring.model';
import { TailoringApiService } from '../../services/tailoring-api.service';
import { TailoringDetailComponent } from './tailoring-detail.component';

describe('TailoringDetailComponent', () => {
  let fixture: ComponentFixture<TailoringDetailComponent>;
  let tailoringApiSpy: jasmine.SpyObj<TailoringApiService>;

  function pendingDetail(overrides: Partial<TailoringPlanDetail> = {}): TailoringPlanDetail {
    return {
      id: 'plan-1',
      analysis_id: 'analysis-1',
      mode: 'CONSERVATIVE',
      engine_version: '1.0.0',
      status: 'PENDING',
      before_score: null,
      after_score: null,
      operations: [],
      protected_fact_ids: [],
      requirements_improved: 0,
      requirements_unchanged: 0,
      requirements_still_missing: 0,
      changes: [],
      error_message: null,
      created_at: '',
      completed_at: null,
      ...overrides,
    };
  }

  function completedDetail(overrides: Partial<TailoringPlanDetail> = {}): TailoringPlanDetail {
    return {
      ...pendingDetail({ status: 'COMPLETED', before_score: 0.72, after_score: 0.81 }),
      requirements_improved: 2,
      requirements_unchanged: 6,
      requirements_still_missing: 3,
      changes: [
        {
          fact_id: 'experience:0',
          recommendation_title: 'Make existing experience match: REST APIs',
          original_text: 'Built internal tooling.',
          final_text: 'Built internal tooling using REST APIs.',
          diff: [
            { text: 'Built internal tooling', change_type: 'UNCHANGED' },
            { text: 'using REST APIs', change_type: 'ADDED' },
          ],
          accepted: true,
          rejection_reasons: [],
        },
      ],
      completed_at: '2026-01-01T00:00:00Z',
      ...overrides,
    };
  }

  function setup(): void {
    tailoringApiSpy = jasmine.createSpyObj('TailoringApiService', ['getPlan', 'getStatus']);
    TestBed.configureTestingModule({
      imports: [TailoringDetailComponent],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([]),
        { provide: TailoringApiService, useValue: tailoringApiSpy },
        { provide: ActivatedRoute, useValue: { snapshot: { paramMap: convertToParamMap({ id: 'plan-1' }) } } },
      ],
    });
    fixture = TestBed.createComponent(TailoringDetailComponent);
  }

  it(
    'shows the progress timeline while the plan is not yet done',
    fakeAsync(() => {
      setup();
      tailoringApiSpy.getPlan.and.returnValue(of(pendingDetail()));
      tailoringApiSpy.getStatus.and.returnValue(
        of({ id: 'plan-1', status: 'GENERATING', error: null, completed_at: null } as TailoringStatusResponse),
      );

      fixture.detectChanges();
      tick();
      fixture.detectChanges();

      const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
      expect(text).toContain('Rewriting selected sections');
      discardPeriodicTasks();
    }),
  );

  it(
    'shows before/after scores and the disclaimer once completed',
    fakeAsync(() => {
      setup();
      tailoringApiSpy.getPlan.and.returnValues(of(pendingDetail()), of(completedDetail()));
      tailoringApiSpy.getStatus.and.returnValue(
        of({ id: 'plan-1', status: 'COMPLETED', error: null, completed_at: '2026-01-01' } as TailoringStatusResponse),
      );

      fixture.detectChanges();
      tick();
      fixture.detectChanges();

      const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
      expect(text).toContain('72');
      expect(text).toContain('81');
      expect(text.toLowerCase()).toContain('does not guarantee');
    }),
  );

  it(
    'shows a human-readable error state on failure',
    fakeAsync(() => {
      setup();
      tailoringApiSpy.getPlan.and.returnValue(of(pendingDetail()));
      tailoringApiSpy.getStatus.and.returnValue(
        of({
          id: 'plan-1',
          status: 'FAILED',
          error: 'An unexpected error occurred while generating the tailored CV.',
          completed_at: '2026-01-01',
        } as TailoringStatusResponse),
      );

      fixture.detectChanges();
      tick();
      fixture.detectChanges();

      const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
      expect(text).toContain('This tailoring run could not be completed');
      expect(text).toContain('An unexpected error occurred while generating the tailored CV.');
    }),
  );

  it(
    'lists changes and reports the accepted/rejected validation summary',
    fakeAsync(() => {
      setup();
      const rejected = completedDetail({
        changes: [
          ...completedDetail().changes,
          {
            fact_id: 'skill:0',
            recommendation_title: 'Hallucinated change',
            original_text: 'Docker',
            final_text: 'Docker',
            diff: [{ text: 'Docker', change_type: 'UNCHANGED' }],
            accepted: false,
            rejection_reasons: ['UNSUPPORTED_TECHNOLOGY'],
          },
        ],
      });
      tailoringApiSpy.getPlan.and.returnValues(of(pendingDetail()), of(rejected));
      tailoringApiSpy.getStatus.and.returnValue(
        of({ id: 'plan-1', status: 'COMPLETED', error: null, completed_at: '2026-01-01' } as TailoringStatusResponse),
      );

      fixture.detectChanges();
      tick();
      fixture.detectChanges();

      const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
      expect(text).toContain('1 change verified');
      expect(text).toContain('1 proposed change could not be verified');
    }),
  );
});
