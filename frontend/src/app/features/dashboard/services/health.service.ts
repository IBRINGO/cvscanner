import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiClientService } from '../../../core/http/api-client.service';
import { HealthResponse } from '../models/health.model';

@Injectable({ providedIn: 'root' })
export class HealthService {
  constructor(private readonly api: ApiClientService) {}

  check(): Observable<HealthResponse> {
    return this.api.get<HealthResponse>('health/');
  }
}
