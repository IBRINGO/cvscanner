import { ChangeDetectionStrategy, Component, Input, signal } from '@angular/core';
import { NgIcon, provideIcons } from '@ng-icons/core';
import { CVSCANNER_ICONS } from '../../../../core/icons';
import { Evidence, SkillRef } from '../../../models/evidence.model';
import { EvidenceNoteComponent } from '../evidence-note/evidence-note.component';
import { SkillRelationsPanelComponent } from '../../../../features/skills/components/skill-relations-panel/skill-relations-panel.component';

/**
 * Displays one extracted skill mention. Deliberately avoids any
 * green/red match coloring (section 46/52) - this is a profile
 * intelligence view, not an ATS score view. A solid border means the
 * taxonomy recognized the term (canonical); a dashed border means it is
 * kept as-is, unrecognized - a factual distinction, not a judgment.
 *
 * Two independent, lazily-loaded expansions live under one chip: the
 * evidence quote (already extracted, free) and the relationship panel
 * (a network call, fetched only the first time it is opened - section
 * 46/66).
 */
@Component({
  selector: 'app-skill-chip',
  standalone: true,
  imports: [EvidenceNoteComponent, SkillRelationsPanelComponent, NgIcon],
  viewProviders: [provideIcons(CVSCANNER_ICONS)],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="skill-chip-group">
      <button
        type="button"
        class="skill-chip"
        [attr.data-matched]="!!skill"
        [attr.aria-expanded]="evidenceExpanded()"
        (click)="toggleEvidence()"
      >
        <ng-icon [name]="skill ? 'lucideCircleCheck' : 'lucideCircleDashed'" size="13" />
        {{ skill?.canonical_name ?? rawText }}
        @if (skill && skill.canonical_name !== rawText) {
          <span class="skill-chip__alias">({{ rawText }})</span>
        }
      </button>
      @if (skill) {
        <button
          type="button"
          class="skill-chip__relations-toggle"
          [attr.aria-expanded]="relationsExpanded()"
          [attr.aria-label]="'Show skills related to ' + skill.canonical_name"
          (click)="toggleRelations()"
        >
          <ng-icon name="lucideNetwork" size="13" />
        </button>
      }
    </div>
    @if (evidenceExpanded() && evidence) {
      <div class="skill-chip__panel">
        <app-evidence-note [evidence]="evidence" />
      </div>
    }
    @if (relationsExpanded() && skill) {
      <div class="skill-chip__panel">
        <app-skill-relations-panel [canonicalName]="skill.canonical_name" />
      </div>
    }
  `,
  styles: [
    `
      .skill-chip-group {
        display: inline-flex;
        align-items: stretch;
        gap: 1px;
      }
      .skill-chip {
        font: inherit;
        cursor: pointer;
        display: inline-flex;
        align-items: center;
        gap: var(--space-1);
        padding: 4px var(--space-3);
        border-radius: var(--radius-pill) 0 0 var(--radius-pill);
        background: var(--surface-raised);
        border: 1px solid var(--border-strong);
        border-right: none;
        color: var(--ink-primary);
        font-size: var(--text-sm);
        transition: border-color var(--motion-fast) var(--motion-ease);
      }
      .skill-chip-group:has(.skill-chip:only-child) .skill-chip {
        border-radius: var(--radius-pill);
        border-right: 1px solid var(--border-strong);
      }
      .skill-chip[data-matched='false'] {
        border-style: dashed;
        color: var(--ink-secondary);
      }
      .skill-chip:hover {
        border-color: var(--accent);
      }
      .skill-chip__relations-toggle {
        cursor: pointer;
        display: inline-flex;
        align-items: center;
        padding: 0 var(--space-2);
        border-radius: 0 var(--radius-pill) var(--radius-pill) 0;
        background: var(--surface-raised);
        border: 1px solid var(--border-strong);
        color: var(--ink-tertiary);
        transition: border-color var(--motion-fast) var(--motion-ease), color var(--motion-fast) var(--motion-ease);
      }
      .skill-chip__relations-toggle:hover,
      .skill-chip__relations-toggle[aria-expanded='true'] {
        border-color: var(--accent);
        color: var(--accent);
      }
      .skill-chip__alias {
        color: var(--ink-tertiary);
        font-size: var(--text-xs);
      }
      .skill-chip__panel {
        margin-top: var(--space-2);
      }
    `,
  ],
})
export class SkillChipComponent {
  @Input({ required: true }) rawText!: string;
  @Input() skill: SkillRef | null = null;
  @Input() evidence: Evidence | null = null;

  protected readonly evidenceExpanded = signal(false);
  protected readonly relationsExpanded = signal(false);

  toggleEvidence(): void {
    if (this.evidence) {
      this.evidenceExpanded.update((value) => !value);
    }
  }

  toggleRelations(): void {
    this.relationsExpanded.update((value) => !value);
  }
}
