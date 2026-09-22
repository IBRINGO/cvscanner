import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed, discardPeriodicTasks, fakeAsync, tick } from '@angular/core/testing';
import { ActivatedRoute, convertToParamMap } from '@angular/router';
import { of } from 'rxjs';
import { DocumentStatusResponse } from '../../../../shared/models/document.model';
import { CandidateProfile } from '../../models/candidate-profile.model';
import { CvApiService } from '../../services/cv-api.service';
import { CvDetailComponent } from './cv-detail.component';

describe('CvDetailComponent', () => {
  let fixture: ComponentFixture<CvDetailComponent>;
  let cvApiSpy: jasmine.SpyObj<CvApiService>;

  function setup(documentId = 'doc-1'): void {
    cvApiSpy = jasmine.createSpyObj('CvApiService', ['getStatus', 'getProfile']);

    TestBed.configureTestingModule({
      imports: [CvDetailComponent],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: CvApiService, useValue: cvApiSpy },
        {
          provide: ActivatedRoute,
          useValue: { snapshot: { paramMap: convertToParamMap({ id: documentId }) } },
        },
      ],
    });

    fixture = TestBed.createComponent(CvDetailComponent);
  }

  it(
    'shows the processing timeline while the document is not yet done',
    fakeAsync(() => {
      setup();
      const status: DocumentStatusResponse = {
        id: 'doc-1',
        status: 'PROCESSING',
        error: null,
        updated_at: '',
      };
      cvApiSpy.getStatus.and.returnValue(of(status));

      fixture.detectChanges();
      tick();
      fixture.detectChanges();

      const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
      expect(text).toContain('Reading your document');
      expect(cvApiSpy.getProfile).not.toHaveBeenCalled();
      discardPeriodicTasks(); // polling never completes while status is PROCESSING
    }),
  );

  it(
    'fetches and renders the profile once processing completes',
    fakeAsync(() => {
      setup();
      cvApiSpy.getStatus.and.returnValue(
        of({ id: 'doc-1', status: 'PROCESSED', error: null, updated_at: '' }),
      );
      const profile: CandidateProfile = {
        full_name: 'Alex Doe',
        email: null,
        phone: null,
        location: null,
        links: [],
        summary: null,
        experiences: [],
        education: [],
        projects: [],
        certifications: [],
        languages: [],
        skills: [],
      };
      cvApiSpy.getProfile.and.returnValue(of({ document_id: 'doc-1', status: 'PROCESSED', profile }));

      fixture.detectChanges();
      tick();
      fixture.detectChanges();

      expect(cvApiSpy.getProfile).toHaveBeenCalledWith('doc-1');
      const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
      expect(text).toContain('Alex Doe');
    }),
  );

  it(
    'shows the error message when processing fails',
    fakeAsync(() => {
      setup();
      cvApiSpy.getStatus.and.returnValue(
        of({ id: 'doc-1', status: 'FAILED', error: 'Corrupted PDF', updated_at: '' }),
      );

      fixture.detectChanges();
      tick();
      fixture.detectChanges();

      const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
      expect(text).toContain('We could not process this document');
      expect(text).toContain('Corrupted PDF');
      expect(cvApiSpy.getProfile).not.toHaveBeenCalled();
    }),
  );
});
