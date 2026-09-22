import { InjectionToken } from '@angular/core';
import { environment } from '../../../environments/environment';

/**
 * Single source of truth for runtime configuration. Nothing outside this
 * file (and the environment files it wraps) should know about
 * `environment.ts` — features/services must inject `APP_CONFIG` instead of
 * hardcoding URLs.
 */
export interface AppConfig {
  readonly production: boolean;
  readonly apiBaseUrl: string;
}

export const APP_CONFIG = new InjectionToken<AppConfig>('APP_CONFIG');

export const appConfigProvider = {
  provide: APP_CONFIG,
  useValue: environment satisfies AppConfig,
};
