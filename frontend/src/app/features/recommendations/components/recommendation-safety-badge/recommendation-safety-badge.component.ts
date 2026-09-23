import { ChangeDetectionStrategy, Component, Input } from '@angular/core';
import { NgIcon, provideIcons } from '@ng-icons/core';
import { CVSCANNER_ICONS } from '../../../../core/icons';
import { RecommendationSafety } from '../../models/recommendation.model';

interface SafetyPresentation {
  icon: string;
  label: string;
  tone: 'positive' | 'attention' | 'negative';
}

/**
 * The trust indicator for a recommendation's automation safety (Phase 5
 * section 46) - icon + label + color together, never color alone,
 * mirroring app-match-signal-badge's contract from Phase 4 exactly so
 * the two badge systems read as one visual language.
 */
const PRESENTATION: Record<RecommendationSafety, SafetyPresentation> = {
  SAFE_TO_REPHRASE: { icon: 'lucideCircleCheck', label: 'Safe to rephrase', tone: 'positive' },
  SAFE_TO_REORDER: { icon: 'lucideCircleCheck', label: 'Safe to reorder', tone: 'positive' },
  REQUIRES_CANDIDATE_CONFIRMATION: {
    icon: 'lucideCircleHelp',
    label: 'Needs your confirmation',
    tone: 'attention',
  },
  NOT_SAFE_TO_AUTOMATE: { icon: 'lucideCircleX', label: 'Not supported by evidence', tone: 'negative' },
};

@Component({
  selector: 'app-recommendation-safety-badge',
  standalone: true,
  imports: [NgIcon],
  viewProviders: [provideIcons(CVSCANNER_ICONS)],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <span class="safety-badge" [attr.data-tone]="presentation.tone" role="status">
      <ng-icon [name]="presentation.icon" size="14" />
      {{ presentation.label }}
    </span>
  `,
  styles: [
    `
      .safety-badge {
        display: inline-flex;
        align-items: center;
        gap: var(--space-1);
        padding: 2px var(--space-2);
        border-radius: var(--radius-sm);
        font-size: var(--text-xs);
        font-weight: 500;
        white-space: nowrap;
      }
      .safety-badge[data-tone='positive'] {
        color: var(--match-positive);
        background: var(--match-positive-tint);
      }
      .safety-badge[data-tone='attention'] {
        color: var(--match-attention);
        background: var(--match-attention-tint);
      }
      .safety-badge[data-tone='negative'] {
        color: var(--match-negative);
        background: var(--match-negative-tint);
      }
    `,
  ],
})
export class RecommendationSafetyBadgeComponent {
  @Input({ required: true }) safety!: RecommendationSafety;

  get presentation(): SafetyPresentation {
    return PRESENTATION[this.safety];
  }
}
