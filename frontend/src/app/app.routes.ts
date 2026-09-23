import { Routes } from '@angular/router';
import { MainLayoutComponent } from './layout/main-layout/main-layout.component';

export const routes: Routes = [
  {
    path: '',
    component: MainLayoutComponent,
    children: [
      { path: '', redirectTo: 'dashboard', pathMatch: 'full' },
      {
        path: 'dashboard',
        loadComponent: () =>
          import('./features/dashboard/pages/dashboard-page/dashboard-page.component').then(
            (m) => m.DashboardPageComponent,
          ),
      },
      {
        path: 'cvs',
        loadComponent: () =>
          import('./features/cvs/pages/cv-list/cv-list.component').then((m) => m.CvListComponent),
      },
      {
        path: 'cvs/:id',
        loadComponent: () =>
          import('./features/cvs/pages/cv-detail/cv-detail.component').then(
            (m) => m.CvDetailComponent,
          ),
      },
      {
        path: 'jobs',
        loadComponent: () =>
          import('./features/jobs/pages/job-list/job-list.component').then(
            (m) => m.JobListComponent,
          ),
      },
      {
        path: 'jobs/:id',
        loadComponent: () =>
          import('./features/jobs/pages/job-detail/job-detail.component').then(
            (m) => m.JobDetailComponent,
          ),
      },
      {
        path: 'analysis',
        loadComponent: () =>
          import('./features/analysis/pages/analysis-list/analysis-list.component').then(
            (m) => m.AnalysisListComponent,
          ),
      },
      {
        path: 'analysis/:id',
        loadComponent: () =>
          import('./features/analysis/pages/analysis-detail/analysis-detail.component').then(
            (m) => m.AnalysisDetailComponent,
          ),
      },
      {
        path: 'analysis/:id/recommendations',
        loadComponent: () =>
          import(
            './features/recommendations/pages/recommendations-page/recommendations-page.component'
          ).then((m) => m.RecommendationsPageComponent),
      },
      // The generic nav entries have no single analysis to show - Phase 5's
      // recommendations/tailoring are always scoped to one analysis, so the
      // real entry point is picking one from the analysis workspace.
      { path: 'recommendations', redirectTo: 'analysis', pathMatch: 'full' },
      { path: 'tailoring', redirectTo: 'analysis', pathMatch: 'full' },
      {
        path: 'tailoring/:id',
        loadComponent: () =>
          import('./features/tailoring/pages/tailoring-detail/tailoring-detail.component').then(
            (m) => m.TailoringDetailComponent,
          ),
      },
      {
        path: 'applications',
        loadComponent: () =>
          import(
            './features/applications/pages/application-list/application-list.component'
          ).then((m) => m.ApplicationListComponent),
      },
      {
        path: 'settings',
        loadComponent: () =>
          import('./features/settings/pages/settings-page/settings-page.component').then(
            (m) => m.SettingsPageComponent,
          ),
      },
    ],
  },
  { path: '**', redirectTo: '' },
];
