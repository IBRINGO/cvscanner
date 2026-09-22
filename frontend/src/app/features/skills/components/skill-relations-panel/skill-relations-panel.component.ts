import { ChangeDetectionStrategy, Component, Input, OnInit, signal } from '@angular/core';
import { NgIcon, provideIcons } from '@ng-icons/core';
import { catchError, of } from 'rxjs';
import { CVSCANNER_ICONS } from '../../../../core/icons';
import { SkillApiService } from '../../services/skill-api.service';
import { RelatedSkill, SkillDetail } from '../../models/skill.model';

type PanelState = 'loading' | 'ready' | 'error';

const RELATION_LABELS: Record<string, string> = {
  PARENT_OF: 'Extended by',
  CHILD_OF: 'Part of',
  PART_OF_ECOSYSTEM: 'Ecosystem',
  RELATED_TO: 'Related',
  ALTERNATIVE_TO: 'Alternative to',
  BUILDS_ON: 'Builds on',
};

/**
 * Lazily-loaded relationship view for one skill (Phase 3 section 46):
 * parent/children/ecosystem siblings/explicit relations, fetched only
 * when a skill chip is expanded - never prefetched for every chip on a
 * page (section 66). A relationship is never a claim of equivalence -
 * see domain/skills/relationships.py on the backend for the source of
 * truth this mirrors.
 */
@Component({
  selector: 'app-skill-relations-panel',
  standalone: true,
  imports: [NgIcon],
  viewProviders: [provideIcons(CVSCANNER_ICONS)],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    @switch (state()) {
      @case ('loading') {
        <div class="relations-panel relations-panel--loading">
          <ng-icon name="lucideLoaderCircle" class="spin" />
          <span>Loading related skills...</span>
        </div>
      }
      @case ('error') {
        <div class="relations-panel relations-panel--error">
          <ng-icon name="lucideTriangleAlert" />
          <span>Couldn't load related skills.</span>
        </div>
      }
      @case ('ready') {
        @if (hasAnyRelation()) {
          <div class="relations-panel">
            @if (detail()!.parent) {
              <div class="relations-panel__group">
                <span class="relations-panel__label">{{ relationLabel('CHILD_OF') }}</span>
                <span class="relations-panel__chip">{{ detail()!.parent!.canonical_name }}</span>
              </div>
            }
            @if (detail()!.children.length > 0) {
              <div class="relations-panel__group">
                <span class="relations-panel__label">{{ relationLabel('PARENT_OF') }}</span>
                @for (child of detail()!.children; track child.canonical_name) {
                  <span class="relations-panel__chip">{{ child.canonical_name }}</span>
                }
              </div>
            }
            @if (detail()!.ecosystem_siblings.length > 0) {
              <div class="relations-panel__group">
                <span class="relations-panel__label">{{ detail()!.ecosystem ?? relationLabel('PART_OF_ECOSYSTEM') }}</span>
                @for (sibling of detail()!.ecosystem_siblings; track sibling.canonical_name) {
                  <span class="relations-panel__chip">{{ sibling.canonical_name }}</span>
                }
              </div>
            }
            @for (group of explicitGroups(); track group.type) {
              <div class="relations-panel__group">
                <span class="relations-panel__label">{{ relationLabel(group.type) }}</span>
                @for (related of group.items; track related.skill.canonical_name) {
                  <span class="relations-panel__chip">{{ related.skill.canonical_name }}</span>
                }
              </div>
            }
          </div>
        } @else {
          <p class="relations-panel__empty">No recorded relationships for this skill yet.</p>
        }
      }
    }
  `,
  styles: [
    `
      .relations-panel {
        display: flex;
        flex-direction: column;
        gap: var(--space-2);
        animation: relations-panel-in var(--motion-base) var(--motion-ease);
      }
      .relations-panel--loading,
      .relations-panel--error {
        flex-direction: row;
        align-items: center;
        gap: var(--space-2);
        color: var(--ink-tertiary);
        font-size: var(--text-sm);
      }
      .relations-panel__group {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: var(--space-2);
      }
      .relations-panel__label {
        font-size: var(--text-xs);
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: var(--ink-tertiary);
        min-width: 88px;
      }
      .relations-panel__chip {
        font-size: var(--text-xs);
        font-family: var(--font-mono);
        color: var(--ink-secondary);
        background: var(--surface-sunken);
        padding: 2px var(--space-2);
        border-radius: var(--radius-sm);
      }
      .relations-panel__empty {
        margin: 0;
        font-size: var(--text-sm);
        color: var(--ink-tertiary);
      }
      .spin {
        animation: relations-panel-spin 0.8s linear infinite;
      }
      @keyframes relations-panel-in {
        from {
          opacity: 0;
          transform: translateY(-2px);
        }
        to {
          opacity: 1;
          transform: translateY(0);
        }
      }
      @keyframes relations-panel-spin {
        to {
          transform: rotate(360deg);
        }
      }
      @media (prefers-reduced-motion: reduce) {
        .relations-panel,
        .spin {
          animation: none;
        }
      }
    `,
  ],
})
export class SkillRelationsPanelComponent implements OnInit {
  @Input({ required: true }) canonicalName!: string;

  protected readonly state = signal<PanelState>('loading');
  protected readonly detail = signal<SkillDetail | null>(null);

  constructor(private readonly skillApi: SkillApiService) {}

  ngOnInit(): void {
    this.state.set('loading');
    this.detail.set(null);
    this.skillApi
      .get(this.canonicalName)
      .pipe(catchError(() => of(null)))
      .subscribe((detail) => {
        if (detail) {
          this.detail.set(detail);
          this.state.set('ready');
        } else {
          this.state.set('error');
        }
      });
  }

  relationLabel(type: string): string {
    return RELATION_LABELS[type] ?? type;
  }

  hasAnyRelation(): boolean {
    const detail = this.detail();
    if (!detail) return false;
    return !!detail.parent || detail.children.length > 0 || detail.ecosystem_siblings.length > 0 || detail.explicit.length > 0;
  }

  explicitGroups(): { type: string; items: RelatedSkill[] }[] {
    const detail = this.detail();
    if (!detail) return [];
    const groups = new Map<string, RelatedSkill[]>();
    for (const related of detail.explicit) {
      const list = groups.get(related.relation_type) ?? [];
      list.push(related);
      groups.set(related.relation_type, list);
    }
    return Array.from(groups.entries()).map(([type, items]) => ({ type, items }));
  }
}
