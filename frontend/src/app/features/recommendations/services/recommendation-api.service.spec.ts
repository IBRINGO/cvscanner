import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { APP_CONFIG } from '../../../core/config/app-config';
import { RecommendationApiService } from './recommendation-api.service';

describe('RecommendationApiService', () => {
  let service: RecommendationApiService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: APP_CONFIG, useValue: { apiBaseUrl: 'http://test/api/v1' } },
      ],
    });
    service = TestBed.inject(RecommendationApiService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => httpMock.verify());

  it('fetches recommendations for an analysis', () => {
    service.getForAnalysis('analysis-1').subscribe();
    const request = httpMock.expectOne('http://test/api/v1/analyses/analysis-1/recommendations/');
    expect(request.request.method).toBe('GET');
    request.flush([]);
  });
});
