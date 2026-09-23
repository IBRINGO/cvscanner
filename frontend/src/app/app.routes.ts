import { Routes } from '@angular/router';
import { MainLayoutComponent } from './layout/main-layout/main-layout.component';

export const routes: Routes = [
  {
    path: '',
    component: MainLayoutComponent,
    children: [
      { path: '', redirectTo: 'workspace', pathMatch: 'full' },
      {
        path: 'workspace',
        loadComponent: () =>
          import('./features/workspace/pages/workspace-page/workspace-page.component').then(
            (m) => m.WorkspacePageComponent,
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
        path: 'cvs/:id/editor',
        loadComponent: () =>
          import('./features/cvs/pages/cv-editor/cv-editor.component').then(
            (m) => m.CvEditorComponent,
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
      // Recommendations/tailoring are always scoped to one analysis, so
      // the generic nav entries are real hub pages (pick an analysis or
      // past run) rather than a silent redirect to an unrelated page -
      // the nav label must match what the candidate actually sees next.
      {
        path: 'recommendations',
        loadComponent: () =>
          import(
            './features/recommendations/pages/recommendations-hub/recommendations-hub.component'
          ).then((m) => m.RecommendationsHubComponent),
      },
      {
        path: 'tailoring',
        loadComponent: () =>
          import('./features/tailoring/pages/tailoring-hub/tailoring-hub.component').then(
            (m) => m.TailoringHubComponent,
          ),
      },
      {
        path: 'tailoring/:id',
        loadComponent: () =>
          import('./features/tailoring/pages/tailoring-detail/tailoring-detail.component').then(
            (m) => m.TailoringDetailComponent,
          ),
      },
      {
        path: 'applications/new',
        loadComponent: () =>
          import(
            './features/applications/pages/new-application/new-application.component'
          ).then((m) => m.NewApplicationComponent),
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
