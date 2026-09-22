import { Injectable } from '@angular/core';

/**
 * Triggers a browser download for an already-fetched Blob (e.g. a
 * generated CV or exported report). Kept separate from FileUploadService
 * since the two are used at opposite ends of a request.
 */
@Injectable({ providedIn: 'root' })
export class DownloadService {
  saveBlob(blob: Blob, filename: string): void {
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.click();
    URL.revokeObjectURL(url);
  }
}
