import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiClientService } from '../../../core/http/api-client.service';
import {
  TailoringMode,
  TailoringPlanDetail,
  TailoringPlanSummary,
  TailoringStatusResponse,
} from '../models/tailoring.model';

@Injectable({ providedIn: 'root' })
export class TailoringApiService {
  constructor(private readonly api: ApiClientService) {}

  create(
    analysisId: string,
    mode: TailoringMode,
    recommendationIds: string[],
  ): Observable<TailoringPlanSummary> {
    return this.api.post<TailoringPlanSummary>('tailoring/', {
      analysis_id: analysisId,
      mode,
      recommendation_ids: recommendationIds,
    });
  }

  list(): Observable<TailoringPlanSummary[]> {
    return this.api.get<TailoringPlanSummary[]>('tailoring/');
  }

  getPlan(planId: string): Observable<TailoringPlanDetail> {
    return this.api.get<TailoringPlanDetail>(`tailoring/${planId}/`);
  }

  getStatus(planId: string): Observable<TailoringStatusResponse> {
    return this.api.get<TailoringStatusResponse>(`tailoring/${planId}/status/`);
  }

  /** Only removes this tailored-CV run - the analysis it came from, and
   * the CV/job documents behind that analysis, are untouched. */
  delete(planId: string): Observable<void> {
    return this.api.delete<void>(`tailoring/${planId}/`);
  }
}
