import { TestBed } from '@angular/core/testing';
import { ApplicationSessionService } from './application-session.service';

describe('ApplicationSessionService', () => {
  let service: ApplicationSessionService;

  beforeEach(() => {
    try {
      sessionStorage.removeItem('cvscanner.session.application');
    } catch {
      /* ignore */
    }
    TestBed.configureTestingModule({});
    service = TestBed.inject(ApplicationSessionService);
  });

  it('starts a fresh session with only the CV id set', () => {
    service.start('cv-1');
    expect(service.state()).toEqual({
      cvId: 'cv-1',
      jobId: null,
      analysisId: null,
      tailoringId: null,
      templateId: null,
    });
  });

  it('accumulates job, analysis, tailoring and template ids as the journey progresses', () => {
    service.start('cv-1');
    service.setJob('job-1');
    service.setAnalysis('analysis-1');
    service.setTailoring('plan-1');
    service.setTemplate('modern-split');

    expect(service.state()).toEqual({
      cvId: 'cv-1',
      jobId: 'job-1',
      analysisId: 'analysis-1',
      tailoringId: 'plan-1',
      templateId: 'modern-split',
    });
  });

  it('starting a new application resets everything from the previous one', () => {
    service.start('cv-1');
    service.setJob('job-1');
    service.start('cv-2');

    expect(service.state()).toEqual({
      cvId: 'cv-2',
      jobId: null,
      analysisId: null,
      tailoringId: null,
      templateId: null,
    });
  });

  it('persists across a fresh instance (simulating a same-tab reload)', () => {
    service.start('cv-1');
    service.setJob('job-1');

    TestBed.resetTestingModule();
    TestBed.configureTestingModule({});
    const rehydrated = TestBed.inject(ApplicationSessionService);
    expect(rehydrated.state().cvId).toBe('cv-1');
    expect(rehydrated.state().jobId).toBe('job-1');
  });
});
