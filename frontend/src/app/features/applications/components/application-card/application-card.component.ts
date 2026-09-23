import { ChangeDetectionStrategy, Component, Input } from '@angular/core';
import { RouterLink } from '@angular/router';
import { NgIcon, provideIcons } from '@ng-icons/core';
import { CVSCANNER_ICONS } from '../../../../core/icons';
import { ApplicationProgressComponent } from '../../../../shared/components/ui/application-progress/application-progress.component';
import { ApplicationView } from '../../models/application.model';

/**
 * One row in the Workspace/Applications lists: the CV/job pairing, real
 * journey progress, the real score if one exists, and a single clear
 * next action - never a grid of vanity stat cards.
 */
@Component({
  selector: 'app-application-card',
  standalone: true,
  imports: [RouterLink, NgIcon, ApplicationProgressComponent],
  viewProviders: [provideIcons(CVSCANNER_ICONS)],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <article class="app-card">
      <div class="app-card__docs">
        <span class="app-card__doc">
          <span class="app-card__doc-icon">
            <ng-icon name="lucideFileText" size="15" />
          </span>
          {{ app.cv.original_filename }}
        </span>
        <ng-icon name="lucideArrowUpRight" size="13" class="app-card__doc-arrow" />
        <span class="app-card__doc">
          <span class="app-card__doc-icon app-card__doc-icon--job">
            <ng-icon name="lucideBriefcase" size="15" />
          </span>
          {{ app.job.original_filename }}
        </span>
      </div>

      <app-application-progress [current]="app.stage" [completed]="app.completedStages" />

      <div class="app-card__footer">
        @if (app.score !== null) {
          <span class="app-card__score font-mono" [attr.data-band]="scoreBand(app.score)">
            {{ round(app.score * 100) }}
            <span class="text-tertiary">ATS match</span>
          </span>
        } @else {
          <span class="text-tertiary font-mono">{{ app.analysisStatus }}</span>
        }
        <a [routerLink]="app.nextActionLink" class="app-card__action">
          {{ app.nextActionLabel }}
          <ng-icon name="lucideArrowUpRight" size="14" />
        </a>
      </div>
    </article>
  `,
  styles: [
    `
      .app-card {
        display: flex;
        flex-direction: column;
        gap: var(--space-4);
        padding: var(--space-5);
        background: var(--surface-raised);
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-lg);
        box-shadow: var(--shadow-document);
        transition:
          transform var(--motion-base) var(--motion-spring),
          box-shadow var(--motion-base) var(--motion-ease),
          border-color var(--motion-base) var(--motion-ease);
      }
      .app-card:hover {
        transform: translateY(-3px);
        box-shadow: var(--shadow-overlay);
        border-color: var(--border-strong);
      }
      .app-card__docs {
        display: flex;
        align-items: center;
        gap: var(--space-2);
        flex-wrap: wrap;
        font-weight: 500;
        color: var(--ink-primary);
      }
      .app-card__doc {
        display: inline-flex;
        align-items: center;
        gap: var(--space-2);
      }
      .app-card__doc-icon {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 26px;
        height: 26px;
        border-radius: var(--radius-sm);
        background: var(--accent-tint);
        color: var(--accent-strong);
        flex-shrink: 0;
      }
      .app-card__doc-icon--job {
        background: var(--surface-sunken);
        color: var(--ink-secondary);
      }
      .app-card__doc-arrow {
        color: var(--ink-tertiary);
        flex-shrink: 0;
      }
      .app-card__footer {
        display: flex;
        align-items: center;
        justify-content: space-between;
        flex-wrap: wrap;
        gap: var(--space-2) var(--space-3);
        padding-top: var(--space-3);
        border-top: 1px solid var(--border-subtle);
      }
      .app-card__score {
        font-size: var(--text-lg);
        font-weight: 600;
        color: var(--ink-tertiary);
        display: inline-flex;
        align-items: baseline;
        gap: var(--space-2);
        white-space: nowrap;
      }
      .app-card__score[data-band='positive'] {
        color: var(--positive);
      }
      .app-card__score[data-band='accent'] {
        color: var(--accent);
      }
      .app-card__score[data-band='attention'] {
        color: var(--attention);
      }
      .app-card__score[data-band='negative'] {
        color: var(--negative);
      }
      .app-card__action {
        display: inline-flex;
        align-items: center;
        gap: var(--space-1);
        font-size: var(--text-sm);
        font-weight: 600;
        color: var(--accent);
        text-decoration: none;
        white-space: nowrap;
      }
      .app-card__action:hover {
        color: var(--accent-strong);
      }

      @media (prefers-reduced-motion: reduce) {
        .app-card {
          transition: none;
        }
      }
    `,
  ],
})
export class ApplicationCardComponent {
  @Input({ required: true }) app!: ApplicationView;

  protected readonly round = Math.round;

  scoreBand(score: number): 'positive' | 'accent' | 'attention' | 'negative' {
    if (score >= 0.8) return 'positive';
    if (score >= 0.6) return 'accent';
    if (score >= 0.35) return 'attention';
    return 'negative';
  }
}
