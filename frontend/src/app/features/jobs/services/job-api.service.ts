import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiClientService } from '../../../core/http/api-client.service';
import { DocumentStatusResponse, DocumentSummary } from '../../../shared/models/document.model';
import { JobProfileResponse } from '../models/job-profile.model';

@Injectable({ providedIn: 'root' })
export class JobApiService {
  constructor(private readonly api: ApiClientService) {}

  uploadFile(file: File): Observable<DocumentSummary> {
    const formData = new FormData();
    formData.append('file', file);
    return this.api.post<DocumentSummary>('jobs/', formData);
  }

  uploadText(text: string): Observable<DocumentSummary> {
    return this.api.post<DocumentSummary>('jobs/', { text });
  }

  list(): Observable<DocumentSummary[]> {
    return this.api.get<DocumentSummary[]>('jobs/');
  }

  getStatus(documentId: string): Observable<DocumentStatusResponse> {
    return this.api.get<DocumentStatusResponse>(`jobs/${documentId}/status/`);
  }

  getProfile(documentId: string): Observable<JobProfileResponse> {
    return this.api.get<JobProfileResponse>(`jobs/${documentId}/profile/`);
  }
}
