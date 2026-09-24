import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiClientService } from '../../../core/http/api-client.service';
import { DocumentStatusResponse, DocumentSummary } from '../../../shared/models/document.model';
import { CandidateProfile, CvProfileResponse } from '../models/candidate-profile.model';
import { CvSectionRef } from '../models/cv-document.model';

export interface RenderPdfRequest {
  profile: CandidateProfile;
  template_id: string;
  section_order: CvSectionRef[];
  hidden_section_ids: string[];
  group_skills_by_category: boolean;
}

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

  /** Also removes everything derived from this CV server-side (its
   * structured profile, any analysis run against it, recommendations,
   * tailoring plans) - see the backend's DeleteDocument use case. Lets
   * the exact same file be re-uploaded and freshly reprocessed instead
   * of silently reusing the deleted document's old results. */
  delete(documentId: string): Observable<void> {
    return this.api.delete<void>(`cvs/${documentId}/`);
  }

  /** Server-rendered A4 PDF for the editor's live (possibly edited,
   * unsaved) profile - a direct file download, not the browser's print
   * dialog. Rendering happens server-side so the PDF keeps real,
   * selectable text (ATS-friendly), unlike a client-side screenshot. */
  renderPdf(payload: RenderPdfRequest): Observable<Blob> {
    return this.api.postForBlob('cvs/render-pdf/', payload);
  }
}
