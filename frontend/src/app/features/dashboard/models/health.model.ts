export interface HealthResponse {
  status: 'ok';
  service: string;
  version: string;
}

export type BackendStatus = 'loading' | 'available' | 'unavailable';
