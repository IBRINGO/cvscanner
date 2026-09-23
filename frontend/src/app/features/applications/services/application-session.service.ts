import { Injectable, signal } from '@angular/core';

export interface ApplicationSessionState {
  cvId: string | null;
  jobId: string | null;
  analysisId: string | null;
  tailoringId: string | null;
  templateId: string | null;
}

const STORAGE_KEY = 'cvscanner.session.application';
const EMPTY_STATE: ApplicationSessionState = {
  cvId: null,
  jobId: null,
  analysisId: null,
  tailoringId: null,
  templateId: null,
};

/**
 * Persists "what application am I currently working on" across route
 * navigations, using only ids the backend already issues (no new
 * backend resource - section 5: "persist ... using the existing
 * backend resources"). Backed by sessionStorage: it survives a reload
 * within the same tab (so refreshing mid-journey doesn't lose your
 * place) but does not leak into a different tab or persist forever.
 */
@Injectable({ providedIn: 'root' })
export class ApplicationSessionService {
  private readonly _state = signal<ApplicationSessionState>(this.readPersisted());
  readonly state = this._state.asReadonly();

  start(cvId: string): void {
    this.update({ ...EMPTY_STATE, cvId });
  }

  setJob(jobId: string): void {
    this.patch({ jobId });
  }

  setAnalysis(analysisId: string): void {
    this.patch({ analysisId });
  }

  setTailoring(tailoringId: string): void {
    this.patch({ tailoringId });
  }

  setTemplate(templateId: string): void {
    this.patch({ templateId });
  }

  clear(): void {
    this.update(EMPTY_STATE);
  }

  private patch(partial: Partial<ApplicationSessionState>): void {
    this.update({ ...this._state(), ...partial });
  }

  private update(next: ApplicationSessionState): void {
    this._state.set(next);
    this.persist(next);
  }

  private persist(state: ApplicationSessionState): void {
    try {
      sessionStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    } catch {
      // Storage unavailable - the session simply won't survive a
      // reload; the journey's own explicit links still work.
    }
  }

  private readPersisted(): ApplicationSessionState {
    try {
      const raw = sessionStorage.getItem(STORAGE_KEY);
      if (raw) return { ...EMPTY_STATE, ...JSON.parse(raw) };
    } catch {
      // Malformed or unavailable - fall through to a clean state.
    }
    return EMPTY_STATE;
  }
}
