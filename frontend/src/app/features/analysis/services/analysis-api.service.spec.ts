import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { APP_CONFIG } from '../../../core/config/app-config';
import { AnalysisApiService } from './analysis-api.service';

describe('AnalysisApiService', () => {
  let service: AnalysisApiService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: APP_CONFIG, useValue: { apiBaseUrl: 'http://test/api/v1' } },
      ],
    });
    service = TestBed.inject(AnalysisApiService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => httpMock.verify());

  it('posts candidate and job document ids to create an analysis', () => {
    service.createAnalysis('cv-1', 'job-1').subscribe();

    const request = httpMock.expectOne('http://test/api/v1/analyses/');
    expect(request.request.method).toBe('POST');
    expect(request.request.body).toEqual({ candidate_document_id: 'cv-1', job_document_id: 'job-1' });
    request.flush({ id: 'analysis-1' });
  });

  it('lists analyses', () => {
    service.list().subscribe();
    const request = httpMock.expectOne('http://test/api/v1/analyses/');
    expect(request.request.method).toBe('GET');
    request.flush([]);
  });

  it('fetches one analysis by id', () => {
    service.getAnalysis('analysis-1').subscribe();
    const request = httpMock.expectOne('http://test/api/v1/analyses/analysis-1/');
    expect(request.request.method).toBe('GET');
    request.flush({});
  });

  it('fetches analysis status by id', () => {
    service.getAnalysisStatus('analysis-1').subscribe();
    const request = httpMock.expectOne('http://test/api/v1/analyses/analysis-1/status/');
    expect(request.request.method).toBe('GET');
    request.flush({});
  });
});
