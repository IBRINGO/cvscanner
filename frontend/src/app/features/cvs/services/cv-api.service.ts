import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiClientService } from '../../../core/http/api-client.service';
import { DocumentStatusResponse, DocumentSummary } from '../../../shared/models/document.model';
import { CvProfileResponse } from '../models/candidate-profile.model';

/**
 * All CV-related HTTP calls go through this service - components never
 * call ApiClientService/HttpClient directly (section 51).
 */
@Injectable({ providedIn: 'root' })
export class CvApiService {
  constructor(private readonly api: ApiClientService) {}

  upload(file: File): Observable<DocumentSummary> {
    const formData = new FormData();
    formData.append('file', file);
    return this.api.post<DocumentSummary>('cvs/', formData);
  }

  list(): Observable<DocumentSummary[]> {
    return this.api.get<DocumentSummary[]>('cvs/');
  }

  getStatus(documentId: string): Observable<DocumentStatusResponse> {
    return this.api.get<DocumentStatusResponse>(`cvs/${documentId}/status/`);
  }

  getProfile(documentId: string): Observable<CvProfileResponse> {
    return this.api.get<CvProfileResponse>(`cvs/${documentId}/profile/`);
  }
}
