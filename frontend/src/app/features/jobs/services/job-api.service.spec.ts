import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { APP_CONFIG } from '../../../core/config/app-config';
import { JobApiService } from './job-api.service';

describe('JobApiService', () => {
  let service: JobApiService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: APP_CONFIG, useValue: { production: false, apiBaseUrl: '/api/v1' } },
      ],
    });
    service = TestBed.inject(JobApiService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => httpMock.verify());

  it('submits pasted text as JSON to POST /jobs/', () => {
    service.uploadText('Senior Engineer').subscribe();

    const req = httpMock.expectOne('/api/v1/jobs/');
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ text: 'Senior Engineer' });
    req.flush({ id: '1', status: 'UPLOADED' });
  });

  it('uploads a file as multipart form data to POST /jobs/', () => {
    const file = new File(['content'], 'job.pdf', { type: 'application/pdf' });

    service.uploadFile(file).subscribe();

    const req = httpMock.expectOne('/api/v1/jobs/');
    expect(req.request.body instanceof FormData).toBe(true);
    req.flush({ id: '1', status: 'UPLOADED' });
  });

  it('fetches the profile from GET /jobs/:id/profile/', () => {
    service.getProfile('abc').subscribe((response) => {
      expect(response.status).toBe('PROCESSED');
    });

    const req = httpMock.expectOne('/api/v1/jobs/abc/profile/');
    req.flush({ document_id: 'abc', status: 'PROCESSED', profile: null });
  });
});
