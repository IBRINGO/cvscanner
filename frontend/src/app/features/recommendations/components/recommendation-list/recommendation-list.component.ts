import { ChangeDetectionStrategy, Component, computed, EventEmitter, Input, Output, signal } from '@angular/core';
import { NgIcon, provideIcons } from '@ng-icons/core';
import { CVSCANNER_ICONS } from '../../../../core/icons';
import { formatEnumLabel } from '../../../../shared/utils/format-label';
import { Recommendation, RecommendationPriority } from '../../models/recommendation.model';
import { RecommendationSafetyBadgeComponent } from '../recommendation-safety-badge/recommendation-safety-badge.component';

const PRIORITY_ORDER: RecommendationPriority[] = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'];

const PRIORITY_ICON: Record<RecommendationPriority, string> = {
  CRITICAL: 'lucideTriangleAlert',
  HIGH: 'lucideCircleAlert',
  MEDIUM: 'lucideCircleDashed',
  LOW: 'lucideMinus',
};

interface PriorityGroup {
  priority: RecommendationPriority;
  recommendations: Recommendation[];
}

/**
 * The central recommendations component (Phase 5 section 43): grouped
 * by priority, each row expandable to its evidence explorer, with a
 * selection checkbox only where CVScanner can actually act safely
 * (section 45/51) - a NOT_SAFE_TO_AUTOMATE recommendation is shown, but
 * is never selectable, so the candidate can never accidentally ask for
 * something that would require inventing a fact.
 */
@Component({
  selector: 'app-recommendation-list',
  standalone: true,
  imports: [NgIcon, RecommendationSafetyBadgeComponent],
  viewProviders: [provideIcons(CVSCANNER_ICONS)],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    @for (group of groups(); track group.priority; let gi = $index) {
      <section class="priority-group" [style.animation-delay.ms]="gi * 60">
        <h3 class="priority-group__heading" [attr.data-priority]="group.priority">
          <span class="priority-group__icon">
            <ng-icon [name]="priorityIcon(group.priority)" size="14" />
          </span>
          {{ formatEnumLabel(group.priority) }}
          <span class="text-tertiary font-mono">{{ group.recommendations.length }}</span>
        </h3>
        <ul class="recommendation-list">
          @for (recommendation of group.recommendations; track recommendation.id) {
            <li class="recommendation-list__row">
              <div class="recommendation-list__summary">
                @if (recommendation.safe_to_tailor) {
                  <input
                    type="checkbox"
                    class="recommendation-list__checkbox"
                    [attr.aria-label]="'Select: ' + recommendation.title"
                    [checked]="isSelected(recommendation.id)"
                    (change)="toggle(recommendation.id)"
                  />
                } @else {
                  <span class="recommendation-list__checkbox-spacer" aria-hidden="true"></span>
                }
                <button type="button" class="recommendation-list__toggle" (click)="toggleExpanded(recommendation.id)">
                  <span class="recommendation-list__title">{{ recommendation.title }}</span>
                  <app-recommendation-safety-badge [safety]="recommendation.safety" />
                  <ng-icon
                    class="recommendation-list__chevron"
                    [name]="isExpanded(recommendation.id) ? 'lucideChevronDown' : 'lucideChevronRight'"
                    size="16"
                  />
                </button>
              </div>

              @if (isExpanded(recommendation.id)) {
                <div class="recommendation-list__detail">
                  <div class="recommendation-list__field">
                    <span class="recommendation-list__label text-tertiary">Why</span>
                    <p class="recommendation-list__reason">{{ recommendation.reason }}</p>
                  </div>
                  @if (recommendation.supporting_evidence.length > 0) {
                    <div class="recommendation-list__field">
                      <span class="recommendation-list__label text-tertiary">Evidence</span>
                      <ul class="recommendation-list__evidence">
                        @for (item of recommendation.supporting_evidence; track $index) {
                          <li>
                            <figcaption class="text-tertiary font-mono">
                              {{ item.source_label ?? formatEnumLabel(item.source_type) }}
                            </figcaption>
                            <blockquote>{{ item.text }}</blockquote>
                          </li>
                        }
                      </ul>
                    </div>
                  }
                  <div class="recommendation-list__field">
                    <span class="recommendation-list__label text-tertiary">Recommended action</span>
                    <p class="recommendation-list__action">{{ recommendation.suggested_action }}</p>
                  </div>
                </div>
              }
            </li>
          }
        </ul>
      </section>
    }
  `,
  styles: [
    `
      .priority-group {
        margin-bottom: var(--space-5);
        padding: var(--space-5);
        background: var(--surface-raised);
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-lg);
        box-shadow: var(--shadow-document);
        animation: priority-group-in var(--motion-slow) var(--motion-ease) both;
      }
      .priority-group__heading {
        display: flex;
        align-items: center;
        gap: var(--space-2);
        font-size: var(--text-sm);
        text-transform: uppercase;
        letter-spacing: 0.04em;
        color: var(--ink-tertiary);
        padding-bottom: var(--space-3);
        border-bottom: 1px solid var(--border-subtle);
        margin-bottom: var(--space-2);
      }
      .priority-group__icon {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 22px;
        height: 22px;
        border-radius: var(--radius-sm);
        background: var(--surface-sunken);
        color: inherit;
      }
      .priority-group__heading[data-priority='CRITICAL'] {
        color: var(--match-negative);
      }
      .priority-group__heading[data-priority='CRITICAL'] .priority-group__icon {
        background: var(--match-negative-tint);
      }
      .priority-group__heading[data-priority='HIGH'] {
        color: var(--match-attention);
      }
      .priority-group__heading[data-priority='HIGH'] .priority-group__icon {
        background: var(--match-attention-tint);
      }
      .recommendation-list {
        list-style: none;
        margin: 0;
        padding: 0;
      }
      .recommendation-list__row {
        border-bottom: 1px solid var(--border-subtle);
        border-radius: var(--radius-sm);
        margin: 0 calc(var(--space-2) * -1);
        transition: background var(--motion-fast) var(--motion-ease);
      }
      .recommendation-list__row:hover {
        background: var(--surface-sunken);
      }
      .recommendation-list__row:last-child {
        border-bottom: none;
      }
      .recommendation-list__summary {
        display: flex;
        align-items: center;
        gap: var(--space-3);
        padding: var(--space-3) var(--space-2);
      }
      .recommendation-list__checkbox,
      .recommendation-list__checkbox-spacer {
        width: 16px;
        height: 16px;
        flex-shrink: 0;
      }
      .recommendation-list__checkbox {
        accent-color: var(--accent);
        cursor: pointer;
      }
      .recommendation-list__toggle {
        flex: 1;
        display: grid;
        grid-template-columns: 1fr auto 16px;
        align-items: center;
        gap: var(--space-3);
        background: none;
        border: none;
        font: inherit;
        text-align: left;
        cursor: pointer;
        color: var(--ink-primary);
        padding: 0;
      }
      .recommendation-list__title {
        font-weight: 500;
      }
      .recommendation-list__chevron {
        color: var(--ink-tertiary);
      }
      .recommendation-list__detail {
        padding: 0 0 var(--space-5) 28px;
        display: flex;
        flex-direction: column;
        gap: var(--space-4);
        max-width: 65ch;
      }
      .recommendation-list__field {
        display: flex;
        flex-direction: column;
        gap: var(--space-1);
      }
      .recommendation-list__label {
        font-size: var(--text-xs);
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
      }
      .recommendation-list__reason {
        margin: 0;
        color: var(--ink-secondary);
      }
      .recommendation-list__action {
        margin: 0;
        font-size: var(--text-sm);
        color: var(--ink-primary);
        font-weight: 500;
      }
      .recommendation-list__evidence {
        list-style: none;
        margin: 0;
        padding: 0;
        display: flex;
        flex-direction: column;
        gap: var(--space-2);
      }
      .recommendation-list__evidence li {
        padding-left: var(--space-3);
        border-left: 2px solid var(--border-subtle);
      }
      .recommendation-list__evidence figcaption {
        font-size: var(--text-xs);
        margin-bottom: 2px;
      }
      .recommendation-list__evidence blockquote {
        margin: 0;
        font-size: var(--text-sm);
        font-style: italic;
        color: var(--ink-secondary);
      }

      @keyframes priority-group-in {
        from {
          opacity: 0;
          transform: translateY(12px);
        }
        to {
          opacity: 1;
          transform: translateY(0);
        }
      }

      @media (prefers-reduced-motion: reduce) {
        .priority-group {
          animation: none;
        }
        .recommendation-list__row {
          transition: none;
        }
      }

      @media (max-width: 640px) {
        .recommendation-list__toggle {
          grid-template-columns: 1fr 16px;
        }
        .recommendation-list__toggle app-recommendation-safety-badge {
          grid-column: 1 / 2;
          grid-row: 2;
        }
        .recommendation-list__title {
          grid-row: 1;
          grid-column: 1 / 3;
        }
      }
    `,
  ],
})
export class RecommendationListComponent {
  @Input({ required: true }) recommendations!: Recommendation[];
  @Output() selectionChange = new EventEmitter<string[]>();

  private readonly expandedIds = signal<Set<string>>(new Set());
  private readonly selectedIds = signal<Set<string>>(new Set());

  protected readonly groups = computed<PriorityGroup[]>(() => {
    const byPriority = new Map<RecommendationPriority, Recommendation[]>();
    for (const recommendation of this.recommendations ?? []) {
      const list = byPriority.get(recommendation.priority) ?? [];
      list.push(recommendation);
      byPriority.set(recommendation.priority, list);
    }
    return PRIORITY_ORDER.filter((priority) => byPriority.has(priority)).map((priority) => ({
      priority,
      recommendations: byPriority.get(priority)!,
    }));
  });

  isExpanded(id: string): boolean {
    return this.expandedIds().has(id);
  }

  toggleExpanded(id: string): void {
    this.expandedIds.update((current) => {
      const next = new Set(current);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  }

  isSelected(id: string): boolean {
    return this.selectedIds().has(id);
  }

  toggle(id: string): void {
    this.selectedIds.update((current) => {
      const next = new Set(current);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
    this.selectionChange.emit(Array.from(this.selectedIds()));
  }

  formatEnumLabel(value: string): string {
    return formatEnumLabel(value);
  }

  priorityIcon(priority: RecommendationPriority): string {
    return PRIORITY_ICON[priority];
  }
}
