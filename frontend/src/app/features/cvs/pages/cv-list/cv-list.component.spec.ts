import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter, Router } from '@angular/router';
import { of, throwError } from 'rxjs';
import { DocumentSummary } from '../../../../shared/models/document.model';
import { CvApiService } from '../../services/cv-api.service';
import { CvListComponent } from './cv-list.component';

describe('CvListComponent', () => {
  let fixture: ComponentFixture<CvListComponent>;
  let cvApiSpy: jasmine.SpyObj<CvApiService>;
  let router: Router;

  function setup(documents: DocumentSummary[] = []): void {
    cvApiSpy = jasmine.createSpyObj('CvApiService', ['list', 'upload']);
    cvApiSpy.list.and.returnValue(of(documents));

    TestBed.configureTestingModule({
      imports: [CvListComponent],
      providers: [provideHttpClient(), provideHttpClientTesting(), provideRouter([]), { provide: CvApiService, useValue: cvApiSpy }],
    });

    fixture = TestBed.createComponent(CvListComponent);
    router = TestBed.inject(Router);
    fixture.detectChanges();
  }

  it('loads and displays previously uploaded documents', () => {
    setup([
      {
        id: '1',
        document_type: 'CV',
        original_filename: 'resume.pdf',
        mime_type: 'application/pdf',
        file_size: 100,
        status: 'PROCESSED',
        page_count: 1,
        created_at: '2026-01-01T00:00:00Z',
        updated_at: '2026-01-01T00:00:00Z',
      },
    ]);

    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(text).toContain('resume.pdf');
  });

  it('shows an empty state when nothing has been uploaded', () => {
    setup([]);
    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(text).toContain('Nothing uploaded yet');
  });

  it('navigates to the document detail page after a successful upload', () => {
    setup([]);
    const navigateSpy = spyOn(router, 'navigate');
    cvApiSpy.upload.and.returnValue(
      of({
        id: 'new-doc',
        document_type: 'CV',
        original_filename: 'cv.pdf',
        mime_type: 'application/pdf',
        file_size: 10,
        status: 'UPLOADED',
        page_count: null,
        created_at: '',
        updated_at: '',
      }),
    );

    fixture.componentInstance.onFileSelected(new File(['x'], 'cv.pdf'));

    expect(navigateSpy).toHaveBeenCalledWith(['/cvs', 'new-doc']);
  });

  it('stops the uploading indicator and stays on the page when the upload fails', () => {
    setup([]);
    cvApiSpy.upload.and.returnValue(throwError(() => new Error('rejected')));

    fixture.componentInstance.onFileSelected(new File(['x'], 'cv.exe'));
    fixture.detectChanges();

    expect(fixture.componentInstance['uploading']()).toBe(false);
  });
});
