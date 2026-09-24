import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { APP_CONFIG } from '../../../core/config/app-config';
import { CvApiService } from './cv-api.service';

describe('CvApiService', () => {
  let service: CvApiService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: APP_CONFIG, useValue: { production: false, apiBaseUrl: '/api/v1' } },
      ],
    });
    service = TestBed.inject(CvApiService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => httpMock.verify());

  it('uploads a file as multipart form data to POST /cvs/', () => {
    const file = new File(['content'], 'cv.pdf', { type: 'application/pdf' });

    service.upload(file).subscribe();

    const req = httpMock.expectOne('/api/v1/cvs/');
    expect(req.request.method).toBe('POST');
    expect(req.request.body instanceof FormData).toBe(true);
    req.flush({ id: '1', status: 'UPLOADED' });
  });

  it('fetches the document list from GET /cvs/', () => {
    service.list().subscribe((documents) => {
      expect(documents.length).toBe(1);
    });

    const req = httpMock.expectOne('/api/v1/cvs/');
    expect(req.request.method).toBe('GET');
    req.flush([{ id: '1' }]);
  });

  it('fetches status from GET /cvs/:id/status/', () => {
    service.getStatus('abc').subscribe((status) => {
      expect(status.status).toBe('PROCESSED');
    });

    const req = httpMock.expectOne('/api/v1/cvs/abc/status/');
    req.flush({ id: 'abc', status: 'PROCESSED', error: null, updated_at: '' });
  });

  it('fetches the profile from GET /cvs/:id/profile/', () => {
    service.getProfile('abc').subscribe((response) => {
      expect(response.status).toBe('PROCESSED');
    });

    const req = httpMock.expectOne('/api/v1/cvs/abc/profile/');
    req.flush({ document_id: 'abc', status: 'PROCESSED', profile: null });
  });

  it('sends DELETE to /cvs/:id/', () => {
    service.delete('abc').subscribe();

    const req = httpMock.expectOne('/api/v1/cvs/abc/');
    expect(req.request.method).toBe('DELETE');
    req.flush(null);
  });
});
