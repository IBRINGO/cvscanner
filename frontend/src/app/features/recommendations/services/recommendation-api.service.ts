import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiClientService } from '../../../core/http/api-client.service';
import { Recommendation } from '../models/recommendation.model';

@Injectable({ providedIn: 'root' })
export class RecommendationApiService {
  constructor(private readonly api: ApiClientService) {}

  getForAnalysis(analysisId: string): Observable<Recommendation[]> {
    return this.api.get<Recommendation[]>(`analyses/${analysisId}/recommendations/`);
  }
}
