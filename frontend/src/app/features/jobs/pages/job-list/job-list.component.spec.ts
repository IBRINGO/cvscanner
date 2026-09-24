import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { of, throwError } from 'rxjs';
import { DocumentSummary } from '../../../../shared/models/document.model';
import { JobApiService } from '../../services/job-api.service';
import { JobListComponent } from './job-list.component';

describe('JobListComponent', () => {
  let fixture: ComponentFixture<JobListComponent>;
  let jobApiSpy: jasmine.SpyObj<JobApiService>;

  function setup(documents: DocumentSummary[] = []): void {
    jobApiSpy = jasmine.createSpyObj('JobApiService', ['list', 'uploadText', 'uploadFile', 'delete']);
    jobApiSpy.list.and.returnValue(of(documents));

    TestBed.configureTestingModule({
      imports: [JobListComponent],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([]),
        { provide: JobApiService, useValue: jobApiSpy },
      ],
    });

    fixture = TestBed.createComponent(JobListComponent);
    fixture.detectChanges();
  }

  const document: DocumentSummary = {
    id: 'doc-1',
    document_type: 'JOB_OFFER',
    original_filename: 'job-offer.pdf',
    mime_type: 'application/pdf',
    file_size: 100,
    status: 'PROCESSED',
    page_count: 1,
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
  };

  it('loads and displays previously added job offers', () => {
    setup([document]);
    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(text).toContain('job-offer.pdf');
  });

  it('shows an empty state when nothing has been added', () => {
    setup([]);
    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(text).toContain('Nothing added yet');
  });

  it('deletes a job offer after confirmation and removes it from the list', () => {
    setup([document]);
    spyOn(window, 'confirm').and.returnValue(true);
    jobApiSpy.delete.and.returnValue(of(undefined));

    fixture.componentInstance.deleteDocument('doc-1');

    expect(jobApiSpy.delete).toHaveBeenCalledWith('doc-1');
    expect(fixture.componentInstance['documents']()).toEqual([]);
  });

  it('does nothing when the user cancels the confirmation', () => {
    setup([document]);
    spyOn(window, 'confirm').and.returnValue(false);

    fixture.componentInstance.deleteDocument('doc-1');

    expect(jobApiSpy.delete).not.toHaveBeenCalled();
    expect(fixture.componentInstance['documents']()).toEqual([document]);
  });

  it('surfaces an error and keeps the job offer in the list if deletion fails', () => {
    setup([document]);
    spyOn(window, 'confirm').and.returnValue(true);
    jobApiSpy.delete.and.returnValue(throwError(() => new Error('boom')));

    fixture.componentInstance.deleteDocument('doc-1');

    expect(fixture.componentInstance['deleteError']()).toContain('Could not delete');
    expect(fixture.componentInstance['documents']()).toEqual([document]);
  });
});
