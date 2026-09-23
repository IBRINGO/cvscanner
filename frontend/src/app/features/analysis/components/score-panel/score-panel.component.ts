import { ChangeDetectionStrategy, Component, Input } from '@angular/core';
import { NgIcon, provideIcons } from '@ng-icons/core';
import { CVSCANNER_ICONS } from '../../../../core/icons';
import { ScoreGaugeComponent } from '../../../../shared/components/ui/score-gauge/score-gauge.component';
import { formatEnumLabel } from '../../../../shared/utils/format-label';
import { ScoreBreakdown } from '../../models/analysis.model';

const DIMENSION_ICON: Record<string, string> = {
  skills: 'lucideCode',
  experience: 'lucideBriefcase',
  seniority: 'lucideLayers',
  education: 'lucideGraduationCap',
  certifications: 'lucideAward',
  languages: 'lucideLanguages',
  responsibilities: 'lucideListChecks',
  domain: 'lucideNetwork',
};

/**
 * The overall-score presentation: an animated radial gauge - the
 * product's core visual claim is "we measured this" - paired with a
 * plain-language interpretation, then a compact set of horizontal
 * dimension bars using one consistent fill color (never a different
 * color per metric).
 */
@Component({
  selector: 'app-score-panel',
  standalone: true,
  imports: [NgIcon, ScoreGaugeComponent],
  viewProviders: [provideIcons(CVSCANNER_ICONS)],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <section class="score-panel">
      <div class="score-panel__headline">
        <app-score-gauge [score]="breakdown.overall" label="ATS Match" />
        <div class="score-panel__interpretation">
          <p class="score-panel__lead">{{ interpretation() }}</p>
          @if (breakdown.mandatory_gap_penalty > 0) {
            <p class="score-panel__penalty-note">
              <ng-icon name="lucideCircleAlert" size="14" />
              Reduced for {{ mandatoryGapCount }} missing mandatory requirement{{
                mandatoryGapCount === 1 ? '' : 's'
              }}.
            </p>
          }
        </div>
      </div>

      <div class="score-panel__dimensions">
        @for (dimension of breakdown.dimensions; track dimension.name; let i = $index) {
          <div class="score-panel__row" [style.animation-delay.ms]="i * 40">
            <span class="score-panel__row-label">
              <ng-icon [name]="dimensionIcon(dimension.name)" size="14" class="score-panel__row-icon" />
              {{ formatEnumLabel(dimension.name) }}
            </span>
            <div class="score-panel__bar-track">
              <div class="score-panel__bar-fill" [style.width.%]="dimension.score * 100"></div>
            </div>
            <span class="score-panel__row-value font-mono">{{ Math.round(dimension.score * 100) }}</span>
          </div>
        }
      </div>
    </section>
  `,
  styles: [
    `
      .score-panel {
        display: flex;
        flex-direction: column;
        gap: var(--space-6);
      }
      .score-panel__headline {
        display: flex;
        align-items: center;
        gap: var(--space-7);
        flex-wrap: wrap;
      }
      .score-panel__interpretation {
        display: flex;
        flex-direction: column;
        gap: var(--space-2);
        min-width: 220px;
        max-width: 40ch;
      }
      .score-panel__lead {
        font-size: var(--text-md);
      }
      .score-panel__lead {
        margin: 0;
        color: var(--ink-secondary);
        max-width: 46ch;
      }
      .score-panel__penalty-note {
        margin: 0;
        display: inline-flex;
        align-items: center;
        gap: var(--space-1);
        font-size: var(--text-sm);
        color: var(--match-attention);
      }
      .score-panel__dimensions {
        display: flex;
        flex-direction: column;
        gap: var(--space-3);
        max-width: 560px;
      }
      .score-panel__row {
        display: grid;
        grid-template-columns: 148px 1fr 36px;
        align-items: center;
        gap: var(--space-3);
        animation: score-row-in var(--motion-slow) var(--motion-ease) both;
      }
      .score-panel__row-label {
        display: inline-flex;
        align-items: center;
        gap: var(--space-2);
        font-size: var(--text-sm);
        color: var(--ink-secondary);
      }
      .score-panel__row-icon {
        color: var(--ink-tertiary);
        flex-shrink: 0;
      }
      @keyframes score-row-in {
        from {
          opacity: 0;
          transform: translateX(-6px);
        }
        to {
          opacity: 1;
          transform: translateX(0);
        }
      }
      .score-panel__bar-track {
        height: 6px;
        border-radius: var(--radius-sm);
        background: var(--surface-sunken);
        overflow: hidden;
      }
      .score-panel__bar-fill {
        height: 100%;
        background: var(--accent);
        border-radius: var(--radius-sm);
        transition: width var(--motion-slow) var(--motion-ease);
      }
      .score-panel__row-value {
        text-align: right;
        font-size: var(--text-sm);
        color: var(--ink-tertiary);
      }
      @media (prefers-reduced-motion: reduce) {
        .score-panel__bar-fill {
          transition: none;
        }
        .score-panel__row {
          animation: none;
        }
      }
      @media (max-width: 640px) {
        .score-panel__row {
          grid-template-columns: 108px 1fr 32px;
        }
        .score-panel__row-label {
          font-size: var(--text-xs);
        }
      }
    `,
  ],
})
export class ScorePanelComponent {
  @Input({ required: true }) breakdown!: ScoreBreakdown;
  @Input() mandatoryGapCount = 0;

  protected readonly Math = Math;

  percentage(): number {
    return Math.round(this.breakdown.overall * 100);
  }

  interpretation(): string {
    const score = this.percentage();
    if (score >= 80) return 'Strong alignment with this role’s requirements.';
    if (score >= 60) return 'Reasonable alignment, with some gaps worth reviewing.';
    if (score >= 35) return 'Partial alignment; several requirements are not yet evidenced.';
    return 'Limited alignment with this role’s stated requirements.';
  }

  formatEnumLabel(value: string): string {
    return formatEnumLabel(value);
  }

  dimensionIcon(name: string): string {
    return DIMENSION_ICON[name] ?? 'lucideTarget';
  }
}
