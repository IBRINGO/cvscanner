import { DatePipe } from '@angular/common';
import { ChangeDetectionStrategy, Component, OnInit, computed, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { NgIcon, provideIcons } from '@ng-icons/core';
import { forkJoin } from 'rxjs';
import { CVSCANNER_ICONS } from '../../../../core/icons';
import { StatusBadgeComponent } from '../../../../shared/components/ui/status-badge/status-badge.component';
import { DocumentSummary } from '../../../../shared/models/document.model';
import { formatEnumLabel } from '../../../../shared/utils/format-label';
import { AnalysisSummary } from '../../../analysis/models/analysis.model';
import { AnalysisApiService } from '../../../analysis/services/analysis-api.service';
import { ApplicationCardComponent } from '../../../applications/components/application-card/application-card.component';
import { ApplicationView } from '../../../applications/models/application.model';
import { buildApplications, findOrphanDocuments } from '../../../applications/utils/build-applications';
import { CvApiService } from '../../../cvs/services/cv-api.service';
import { JobApiService } from '../../../jobs/services/job-api.service';
import { SkillRef } from '../../../skills/models/skill.model';
import { SkillApiService } from '../../../skills/services/skill-api.service';
import { TailoringApiService } from '../../../tailoring/services/tailoring-api.service';
import { HealthStatusComponent } from '../../components/health-status/health-status.component';

interface SkillDomainCount {
  domain: string;
  count: number;
}

/**
 * The product home: what CVScanner is actually for is the CV -> Job ->
 * Analysis -> Recommendations -> Tailoring -> Export journey, so the
 * home screen leads with real, in-progress applications and a single
 * clear next action each - not a KPI dashboard. "Applications" is a
 * client-side derived view (see build-applications.ts); nothing here is
 * a new backend entity or a fabricated statistic.
 */
@Component({
  selector: 'app-workspace-page',
  standalone: true,
  imports: [
    HealthStatusComponent,
    StatusBadgeComponent,
    ApplicationCardComponent,
    RouterLink,
    DatePipe,
    NgIcon,
  ],
  viewProviders: [provideIcons(CVSCANNER_ICONS)],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <section class="workspace">
      <header class="workspace__header">
        <div>
          <h1>Workspace</h1>
          <p class="text-secondary">Pick up an active application, or start analyzing a new one.</p>
        </div>
        <a routerLink="/applications/new" class="workspace__cta">
          <ng-icon name="lucideScanSearch" size="16" />
          Analyze a new application
        </a>
      </header>

      <section class="workspace__section">
        <h2>Active applications</h2>
        @if (applications().length === 0) {
          <p class="text-secondary">
            No applications yet. Upload a CV and a job offer, then run an analysis to see it here.
          </p>
        } @else {
          <div class="workspace__applications">
            @for (app of applications(); track app.analysisId) {
              <app-application-card [app]="app" />
            }
          </div>
        }
      </section>

      @if (readyCvs().length > 0 || readyJobs().length > 0) {
        <section class="workspace__section">
          <h2>Ready to pair</h2>
          <p class="text-secondary">Processed documents not yet used in an analysis.</p>
          <ul class="workspace__ready-list">
            @for (doc of readyCvs(); track doc.id) {
              <li>
                <ng-icon name="lucideFileText" size="15" />
                <a [routerLink]="['/cvs', doc.id]">{{ doc.original_filename }}</a>
                <span class="text-tertiary">CV ready - add a target job</span>
              </li>
            }
            @for (doc of readyJobs(); track doc.id) {
              <li>
                <ng-icon name="lucideBriefcase" size="15" />
                <a [routerLink]="['/jobs', doc.id]">{{ doc.original_filename }}</a>
                <span class="text-tertiary">Job ready - pair with a CV</span>
              </li>
            }
          </ul>
        </section>
      }

      <div class="workspace__columns">
        <section class="workspace__panel">
          <h2><ng-icon name="lucideFileText" size="18" />Recent CVs</h2>
          @if (recentCvs().length === 0) {
            <p class="text-secondary">
              No CVs yet.
              <a routerLink="/cvs">Upload your first one.</a>
            </p>
          } @else {
            <ul class="workspace__doc-list">
              @for (doc of recentCvs(); track doc.id) {
                <li>
                  <a [routerLink]="['/cvs', doc.id]">{{ doc.original_filename }}</a>
                  <app-status-badge [status]="doc.status" />
                  <span class="text-tertiary font-mono">{{ doc.created_at | date: 'MMM d' }}</span>
                </li>
              }
            </ul>
          }
        </section>

        <section class="workspace__panel">
          <h2><ng-icon name="lucideBriefcase" size="18" />Recent job offers</h2>
          @if (recentJobs().length === 0) {
            <p class="text-secondary">
              No job offers yet.
              <a routerLink="/jobs">Add your first one.</a>
            </p>
          } @else {
            <ul class="workspace__doc-list">
              @for (doc of recentJobs(); track doc.id) {
                <li>
                  <a [routerLink]="['/jobs', doc.id]">{{ doc.original_filename }}</a>
                  <app-status-badge [status]="doc.status" />
                  <span class="text-tertiary font-mono">{{ doc.created_at | date: 'MMM d' }}</span>
                </li>
              }
            </ul>
          }
        </section>
      </div>

      @if (skillDomains().length > 0) {
        <section class="workspace__panel">
          <h2><ng-icon name="lucideLayers" size="18" />Skill taxonomy landscape</h2>
          <p class="text-secondary">
            The categories CVScanner currently recognizes when normalizing skills.
          </p>
          <div class="workspace__domains">
            @for (group of skillDomains(); track group.domain) {
              <div class="workspace__domain">
                <span class="workspace__domain-count">{{ group.count }}</span>
                <span class="text-tertiary">{{ formatEnumLabel(group.domain) }}</span>
              </div>
            }
          </div>
        </section>
      }

      <app-health-status />
    </section>
  `,
  styles: [
    `
      .workspace {
        display: flex;
        flex-direction: column;
        gap: var(--space-7);
        max-width: 1040px;
      }
      .workspace__header {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: var(--space-4);
        flex-wrap: wrap;
      }
      .workspace__header > div {
        display: flex;
        flex-direction: column;
        gap: var(--space-1);
      }
      .workspace__cta {
        display: inline-flex;
        align-items: center;
        gap: var(--space-2);
        padding: var(--space-3) var(--space-5);
        border-radius: var(--radius-md);
        background: var(--accent);
        color: #fff;
        font-weight: 600;
        font-size: var(--text-sm);
        text-decoration: none;
        white-space: nowrap;
        transition: background var(--motion-fast) var(--motion-ease);
      }
      .workspace__cta:hover {
        background: var(--accent-strong);
      }
      .workspace__section {
        display: flex;
        flex-direction: column;
        gap: var(--space-3);
      }
      .workspace__applications {
        display: flex;
        flex-direction: column;
        gap: var(--space-3);
      }
      .workspace__ready-list {
        list-style: none;
        margin: 0;
        padding: 0;
        display: flex;
        flex-direction: column;
        gap: var(--space-2);
      }
      .workspace__ready-list li {
        display: flex;
        align-items: center;
        gap: var(--space-2);
        padding: var(--space-2) 0;
      }
      .workspace__ready-list a {
        color: var(--ink-primary);
        font-weight: 500;
        text-decoration: none;
      }
      .workspace__ready-list a:hover {
        color: var(--accent);
      }
      .workspace__columns {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        gap: var(--space-5);
      }
      .workspace__panel h2 {
        display: flex;
        align-items: center;
        gap: var(--space-2);
        margin-bottom: var(--space-3);
      }
      .workspace__doc-list {
        list-style: none;
        margin: 0;
        padding: 0;
        display: flex;
        flex-direction: column;
        gap: var(--space-3);
      }
      .workspace__doc-list li {
        display: flex;
        align-items: center;
        gap: var(--space-3);
        flex-wrap: wrap;
      }
      .workspace__doc-list a {
        color: var(--ink-primary);
        font-weight: 500;
        text-decoration: none;
      }
      .workspace__doc-list a:hover {
        color: var(--accent);
      }
      .workspace__domains {
        display: flex;
        flex-wrap: wrap;
        gap: var(--space-5);
      }
      .workspace__domain {
        display: flex;
        flex-direction: column;
        gap: 2px;
      }
      .workspace__domain-count {
        font-family: var(--font-display);
        font-size: var(--text-xl);
        color: var(--ink-primary);
      }

      @media (max-width: 640px) {
        .workspace__header {
          flex-direction: column;
          align-items: stretch;
        }
        .workspace__cta {
          justify-content: center;
        }
      }
    `,
  ],
})
export class WorkspacePageComponent implements OnInit {
  protected readonly cvs = signal<DocumentSummary[]>([]);
  protected readonly jobs = signal<DocumentSummary[]>([]);
  protected readonly skills = signal<SkillRef[]>([]);
  protected readonly applications = signal<ApplicationView[]>([]);

  protected readonly recentCvs = computed(() => this.cvs().slice(0, 5));
  protected readonly recentJobs = computed(() => this.jobs().slice(0, 5));
  protected readonly readyCvs = computed(() => this.orphans().cvs.slice(0, 5));
  protected readonly readyJobs = computed(() => this.orphans().jobs.slice(0, 5));
  private readonly analyses = signal<AnalysisSummary[]>([]);
  private readonly orphans = computed(() =>
    findOrphanDocuments(this.cvs(), this.jobs(), this.analyses()),
  );

  protected readonly skillDomains = computed<SkillDomainCount[]>(() => {
    const counts = new Map<string, number>();
    for (const skill of this.skills()) {
      counts.set(skill.domain, (counts.get(skill.domain) ?? 0) + 1);
    }
    return Array.from(counts.entries()).map(([domain, count]) => ({ domain, count }));
  });

  constructor(
    private readonly cvApi: CvApiService,
    private readonly jobApi: JobApiService,
    private readonly skillApi: SkillApiService,
    private readonly analysisApi: AnalysisApiService,
    private readonly tailoringApi: TailoringApiService,
  ) {}

  ngOnInit(): void {
    this.skillApi.list().subscribe((skills) => this.skills.set(skills));

    forkJoin({
      cvs: this.cvApi.list(),
      jobs: this.jobApi.list(),
      analyses: this.analysisApi.list(),
      tailoringPlans: this.tailoringApi.list(),
    }).subscribe(({ cvs, jobs, analyses, tailoringPlans }) => {
      this.cvs.set(cvs);
      this.jobs.set(jobs);
      this.analyses.set(analyses);
      this.applications.set(buildApplications(cvs, jobs, analyses, tailoringPlans));
    });
  }

  formatEnumLabel(value: string): string {
    return formatEnumLabel(value);
  }
}
