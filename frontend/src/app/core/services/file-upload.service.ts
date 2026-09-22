import { HttpClient, HttpEventType } from '@angular/common/http';
import { Inject, Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { filter, map } from 'rxjs/operators';
import { APP_CONFIG, AppConfig } from '../config/app-config';

export interface UploadProgress {
  progress: number; // 0-100
  done: boolean;
}

/**
 * Generic multipart file upload helper with progress reporting.
 * Feature services (e.g. the future `cvs` upload flow) build on this
 * instead of calling HttpClient directly.
 */
@Injectable({ providedIn: 'root' })
export class FileUploadService {
  constructor(
    private readonly http: HttpClient,
    @Inject(APP_CONFIG) private readonly config: AppConfig,
  ) {}

  upload(path: string, file: File, fieldName = 'file'): Observable<UploadProgress> {
    const formData = new FormData();
    formData.append(fieldName, file);

    const normalizedPath = path.startsWith('/') ? path.slice(1) : path;
    const url = `${this.config.apiBaseUrl}/${normalizedPath}`;

    return this.http
      .post(url, formData, { reportProgress: true, observe: 'events' })
      .pipe(
        filter(
          (event) =>
            event.type === HttpEventType.UploadProgress || event.type === HttpEventType.Response,
        ),
        map((event) => {
          if (event.type === HttpEventType.UploadProgress && event.total) {
            return { progress: Math.round((event.loaded / event.total) * 100), done: false };
          }
          return { progress: 100, done: true };
        }),
      );
  }
}
