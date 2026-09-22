import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiClientService } from '../../../core/http/api-client.service';
import { SkillDetail, SkillRef } from '../models/skill.model';

/**
 * All skill-taxonomy HTTP calls go through this service (section 51),
 * mirroring CvApiService/JobApiService. Skill detail is fetched lazily,
 * on demand (section 66) - never prefetched for every chip on a page.
 */
@Injectable({ providedIn: 'root' })
export class SkillApiService {
  constructor(private readonly api: ApiClientService) {}

  list(): Observable<SkillRef[]> {
    return this.api.get<SkillRef[]>('skills/');
  }

  get(canonicalName: string): Observable<SkillDetail> {
    return this.api.get<SkillDetail>(`skills/${encodeURIComponent(canonicalName)}/`);
  }
}
