import { DatePipe } from '@angular/common';
import { ChangeDetectionStrategy, Component, OnInit, computed, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { NgIcon, provideIcons } from '@ng-icons/core';
import { CVSCANNER_ICONS } from '../../../../core/icons';
import { StatusBadgeComponent } from '../../../../shared/components/ui/status-badge/status-badge.component';
import { DocumentSummary } from '../../../../shared/models/document.model';
import { formatEnumLabel } from '../../../../shared/utils/format-label';
import { AnalysisSummary } from '../../../analysis/models/analysis.model';
import { AnalysisApiService } from '../../../analysis/services/analysis-api.service';
import { CvApiService } from '../../../cvs/services/cv-api.service';
import { JobApiService } from '../../../jobs/services/job-api.service';
import { SkillApiService } from '../../../skills/services/skill-api.service';
import { SkillRef } from '../../../skills/models/skill.model';
import { HealthStatusComponent } from '../../components/health-status/health-status.component';

const RECENT_LIMIT = 5;

interface SkillDomainCount {
  domain: string;
  count: number;
}

/**
 * The real product workspace (Phase 3 section 42): recent CVs, recent
 * job offers, and a skill-taxonomy landscape - built from the same
 * endpoints the CVs/Jobs pages already use, not a grid of fabricated
 * statistic cards. No score, percentage, or trend appears anywhere here
 * that isn't a plain count of real rows.
 */
@Component({
  selector: 'app-dashboard-page',
  standalone: true,
  imports: [HealthStatusComponent, StatusBadgeComponent, RouterLink, DatePipe, NgIcon],
  viewProviders: [provideIcons(CVSCANNER_ICONS)],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <section class="dashboard">
      <header class="dashboard__header">
        <h1>Dashboard</h1>
        <p class="text-secondary">An overview of your CVs, job offers, and processing activity.</p>
      </header>

      <div class="dashboard__stats">
        <div class="dashboard__stat">
          <ng-icon name="lucideFileCheck" size="20" />
          <span class="dashboard__stat-value">{{ cvs().length }}</span>
          <span class="text-tertiary">CVs</span>
        </div>
        <div class="dashboard__stat">
          <ng-icon name="lucideBriefcase" size="20" />
          <span class="dashboard__stat-value">{{ jobs().length }}</span>
          <span class="text-tertiary">Job offers</span>
        </div>
        <div class="dashboard__stat">
          <ng-icon name="lucideCircleAlert" size="20" />
          <span class="dashboard__stat-value">{{ needsAttentionCount() }}</span>
          <span class="text-tertiary">Needs attention</span>
        </div>
        <div class="dashboard__stat">
          <ng-icon name="lucideTarget" size="20" />
          <span class="dashboard__stat-value">{{ analyses().length }}</span>
          <span class="text-tertiary">Analyses</span>
        </div>
      </div>

      <div class="dashboard__columns">
        <section class="dashboard__panel">
          <h2><ng-icon name="lucideFileText" size="18" />Recent CVs</h2>
          @if (recentCvs().length === 0) {
            <p class="text-secondary">
              No CVs yet.
              <a routerLink="/cvs">Upload your first one.</a>
            </p>
          } @else {
            <ul class="dashboard__doc-list">
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

        <section class="dashboard__panel">
          <h2><ng-icon name="lucideBriefcase" size="18" />Recent job offers</h2>
          @if (recentJobs().length === 0) {
            <p class="text-secondary">
              No job offers yet.
              <a routerLink="/jobs">Add your first one.</a>
            </p>
          } @else {
            <ul class="dashboard__doc-list">
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

        <section class="dashboard__panel">
          <h2><ng-icon name="lucideTarget" size="18" />Recent analyses</h2>
          @if (recentAnalyses().length === 0) {
            <p class="text-secondary">
              No analyses yet.
              <a routerLink="/analysis">Run your first one.</a>
            </p>
          } @else {
            <ul class="dashboard__doc-list">
              @for (analysis of recentAnalyses(); track analysis.id) {
                <li>
                  <a [routerLink]="['/analysis', analysis.id]">
                    {{ documentName(analysis.candidate_document_id) }} vs
                    {{ documentName(analysis.job_document_id) }}
                  </a>
                  <span class="dashboard__analysis-status" [attr.data-status]="analysis.status">
                    @if (analysis.status === 'COMPLETED' && analysis.overall_score !== null) {
                      {{ round(analysis.overall_score * 100) }}
                    } @else {
                      {{ analysis.status }}
                    }
                  </span>
                  <span class="text-tertiary font-mono">{{ analysis.created_at | date: 'MMM d' }}</span>
                </li>
              }
            </ul>
          }
        </section>
      </div>

      @if (skillDomains().length > 0) {
        <section class="dashboard__panel">
          <h2><ng-icon name="lucideLayers" size="18" />Skill taxonomy landscape</h2>
          <p class="text-secondary">
            The categories CVScanner currently recognizes when normalizing skills.
          </p>
          <div class="dashboard__domains">
            @for (group of skillDomains(); track group.domain) {
              <div class="dashboard__domain">
                <span class="dashboard__domain-count">{{ group.count }}</span>
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
      .dashboard {
        display: flex;
        flex-direction: column;
        gap: var(--space-6);
        max-width: 960px;
      }
      .dashboard__header {
        display: flex;
        flex-direction: column;
        gap: var(--space-1);
      }
      .dashboard__stats {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
        gap: var(--space-4);
      }
      .dashboard__stat {
        display: flex;
        flex-direction: column;
        align-items: flex-start;
        gap: var(--space-1);
        padding: var(--space-4);
        background: var(--surface-raised);
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-md);
        color: var(--ink-tertiary);
      }
      .dashboard__stat-value {
        font-family: var(--font-display);
        font-size: var(--text-2xl);
        color: var(--ink-primary);
      }
      .dashboard__columns {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        gap: var(--space-5);
      }
      .dashboard__panel h2 {
        display: flex;
        align-items: center;
        gap: var(--space-2);
        margin-bottom: var(--space-3);
      }
      .dashboard__doc-list {
        list-style: none;
        margin: 0;
        padding: 0;
        display: flex;
        flex-direction: column;
        gap: var(--space-3);
      }
      .dashboard__doc-list li {
        display: flex;
        align-items: center;
        gap: var(--space-3);
        flex-wrap: wrap;
      }
      .dashboard__doc-list a {
        color: var(--ink-primary);
        font-weight: 500;
        text-decoration: none;
      }
      .dashboard__doc-list a:hover {
        color: var(--accent);
      }
      .dashboard__domains {
        display: flex;
        flex-wrap: wrap;
        gap: var(--space-5);
      }
      .dashboard__domain {
        display: flex;
        flex-direction: column;
        gap: 2px;
      }
      .dashboard__domain-count {
        font-family: var(--font-display);
        font-size: var(--text-xl);
        color: var(--ink-primary);
      }
      .dashboard__analysis-status {
        font-family: var(--font-mono);
        font-size: var(--text-sm);
        color: var(--ink-tertiary);
        white-space: nowrap;
      }
      .dashboard__analysis-status[data-status='COMPLETED'] {
        color: var(--match-positive);
        font-weight: 500;
      }
      .dashboard__analysis-status[data-status='FAILED'] {
        color: var(--match-negative);
      }
    `,
  ],
})
export class DashboardPageComponent implements OnInit {
  protected readonly cvs = signal<DocumentSummary[]>([]);
  protected readonly jobs = signal<DocumentSummary[]>([]);
  protected readonly skills = signal<SkillRef[]>([]);
  protected readonly analyses = signal<AnalysisSummary[]>([]);
  protected readonly round = Math.round;

  protected readonly recentCvs = computed(() => this.cvs().slice(0, RECENT_LIMIT));
  protected readonly recentJobs = computed(() => this.jobs().slice(0, RECENT_LIMIT));
  protected readonly recentAnalyses = computed(() => this.analyses().slice(0, RECENT_LIMIT));
  protected readonly needsAttentionCount = computed(
    () =>
      this.cvs().filter((doc) => doc.status === 'FAILED').length +
      this.jobs().filter((doc) => doc.status === 'FAILED').length,
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
  ) {}

  ngOnInit(): void {
    this.cvApi.list().subscribe((docs) => this.cvs.set(docs));
    this.jobApi.list().subscribe((docs) => this.jobs.set(docs));
    this.skillApi.list().subscribe((skills) => this.skills.set(skills));
    this.analysisApi.list().subscribe((analyses) => this.analyses.set(analyses));
  }

  formatEnumLabel(value: string): string {
    return formatEnumLabel(value);
  }

  documentName(documentId: string): string {
    const match = [...this.cvs(), ...this.jobs()].find((document) => document.id === documentId);
    return match?.original_filename ?? 'Document';
  }
}
