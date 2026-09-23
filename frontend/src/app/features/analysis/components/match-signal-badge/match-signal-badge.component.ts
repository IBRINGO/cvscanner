import { ChangeDetectionStrategy, Component, Input } from '@angular/core';
import { NgIcon, provideIcons } from '@ng-icons/core';
import { CVSCANNER_ICONS } from '../../../../core/icons';
import { MatchSignal } from '../../models/analysis.model';

interface SignalPresentation {
  icon: string;
  label: string;
  tone: 'positive' | 'attention' | 'negative' | 'semantic';
}

/**
 * The single, consistent visual for a match signal (Phase 4 section 48):
 * icon + label + color together, never color alone (section 42/55). One
 * shared mapping so the requirement matrix, gap list, and evidence
 * explorer all render EXACT/ALIAS/RELATED/SEMANTIC/PARTIAL/NO_EVIDENCE
 * identically.
 */
const PRESENTATION: Record<MatchSignal, SignalPresentation> = {
  EXACT_MATCH: { icon: 'lucideCircleCheck', label: 'Exact match', tone: 'positive' },
  ALIAS_MATCH: { icon: 'lucideCircleCheck', label: 'Alias match', tone: 'positive' },
  RELATED_MATCH: { icon: 'lucideGitBranch', label: 'Related match', tone: 'attention' },
  SEMANTIC_MATCH: { icon: 'lucideScanSearch', label: 'Semantic match', tone: 'semantic' },
  PARTIAL_MATCH: { icon: 'lucideCircleDashed', label: 'Partial match', tone: 'attention' },
  NO_EVIDENCE: { icon: 'lucideCircleX', label: 'No evidence', tone: 'negative' },
};

@Component({
  selector: 'app-match-signal-badge',
  standalone: true,
  imports: [NgIcon],
  viewProviders: [provideIcons(CVSCANNER_ICONS)],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <span class="match-signal-badge" [attr.data-tone]="presentation.tone" role="status">
      <ng-icon [name]="presentation.icon" size="14" />
      {{ presentation.label }}
    </span>
  `,
  styles: [
    `
      .match-signal-badge {
        display: inline-flex;
        align-items: center;
        gap: var(--space-1);
        padding: 2px var(--space-2);
        border-radius: var(--radius-sm);
        font-size: var(--text-xs);
        font-weight: 500;
        white-space: nowrap;
      }
      .match-signal-badge[data-tone='positive'] {
        color: var(--match-positive);
        background: var(--match-positive-tint);
      }
      .match-signal-badge[data-tone='attention'] {
        color: var(--match-attention);
        background: var(--match-attention-tint);
      }
      .match-signal-badge[data-tone='negative'] {
        color: var(--match-negative);
        background: var(--match-negative-tint);
      }
      .match-signal-badge[data-tone='semantic'] {
        color: var(--match-semantic);
        background: var(--match-semantic-tint);
      }
    `,
  ],
})
export class MatchSignalBadgeComponent {
  @Input({ required: true }) signal!: MatchSignal;

  get presentation(): SignalPresentation {
    return PRESENTATION[this.signal];
  }
}
