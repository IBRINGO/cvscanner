import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiClientService } from '../../../core/http/api-client.service';
import { AnalysisDetail, AnalysisStatusResponse, AnalysisSummary } from '../models/analysis.model';

/**
 * All analysis-related HTTP calls go through this service (section 51/57)
 * - components never call ApiClientService/HttpClient directly.
 */
@Injectable({ providedIn: 'root' })
export class AnalysisApiService {
  constructor(private readonly api: ApiClientService) {}

  createAnalysis(candidateDocumentId: string, jobDocumentId: string): Observable<AnalysisSummary> {
    return this.api.post<AnalysisSummary>('analyses/', {
      candidate_document_id: candidateDocumentId,
      job_document_id: jobDocumentId,
    });
  }

  list(): Observable<AnalysisSummary[]> {
    return this.api.get<AnalysisSummary[]>('analyses/');
  }

  getAnalysis(analysisId: string): Observable<AnalysisDetail> {
    return this.api.get<AnalysisDetail>(`analyses/${analysisId}/`);
  }

  getAnalysisStatus(analysisId: string): Observable<AnalysisStatusResponse> {
    return this.api.get<AnalysisStatusResponse>(`analyses/${analysisId}/status/`);
  }
}
