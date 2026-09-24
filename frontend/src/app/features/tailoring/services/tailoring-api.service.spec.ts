import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { APP_CONFIG } from '../../../core/config/app-config';
import { TailoringApiService } from './tailoring-api.service';

describe('TailoringApiService', () => {
  let service: TailoringApiService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: APP_CONFIG, useValue: { apiBaseUrl: 'http://test/api/v1' } },
      ],
    });
    service = TestBed.inject(TailoringApiService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => httpMock.verify());

  it('posts analysis id, mode, and recommendation ids to create a plan', () => {
    service.create('analysis-1', 'CONSERVATIVE', ['rec-1', 'rec-2']).subscribe();

    const request = httpMock.expectOne('http://test/api/v1/tailoring/');
    expect(request.request.method).toBe('POST');
    expect(request.request.body).toEqual({
      analysis_id: 'analysis-1',
      mode: 'CONSERVATIVE',
      recommendation_ids: ['rec-1', 'rec-2'],
    });
    request.flush({ id: 'plan-1' });
  });

  it('lists tailoring plans', () => {
    service.list().subscribe();
    httpMock.expectOne('http://test/api/v1/tailoring/').flush([]);
  });

  it('fetches one plan by id', () => {
    service.getPlan('plan-1').subscribe();
    httpMock.expectOne('http://test/api/v1/tailoring/plan-1/').flush({});
  });

  it('fetches plan status by id', () => {
    service.getStatus('plan-1').subscribe();
    httpMock.expectOne('http://test/api/v1/tailoring/plan-1/status/').flush({});
  });

  it('sends DELETE to remove a plan by id', () => {
    service.delete('plan-1').subscribe();
    const req = httpMock.expectOne('http://test/api/v1/tailoring/plan-1/');
    expect(req.request.method).toBe('DELETE');
    req.flush(null);
  });
});
