import { ChangeDetectionStrategy, Component, Input, signal } from '@angular/core';
import { Evidence, SkillRef } from '../../../models/evidence.model';
import { EvidenceNoteComponent } from '../evidence-note/evidence-note.component';

/**
 * Displays one extracted skill mention. Deliberately avoids any
 * green/red match coloring (section 46/52) - this is a profile
 * intelligence view, not an ATS score view. A solid border means the
 * taxonomy recognized the term (canonical); a dashed border means it is
 * kept as-is, unrecognized - a factual distinction, not a judgment.
 */
@Component({
  selector: 'app-skill-chip',
  standalone: true,
  imports: [EvidenceNoteComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <button
      type="button"
      class="skill-chip"
      [attr.data-matched]="!!skill"
      [attr.aria-expanded]="expanded()"
      (click)="toggle()"
    >
      {{ skill?.canonical_name ?? rawText }}
      @if (skill && skill.canonical_name !== rawText) {
        <span class="skill-chip__alias">({{ rawText }})</span>
      }
    </button>
    @if (expanded() && evidence) {
      <div class="skill-chip__evidence">
        <app-evidence-note [evidence]="evidence" />
      </div>
    }
  `,
  styles: [
    `
      .skill-chip {
        font: inherit;
        cursor: pointer;
        display: inline-flex;
        align-items: center;
        gap: var(--space-1);
        padding: 4px var(--space-3);
        border-radius: var(--radius-pill);
        background: var(--surface-raised);
        border: 1px solid var(--border-strong);
        color: var(--ink-primary);
        font-size: var(--text-sm);
      }
      .skill-chip[data-matched='false'] {
        border-style: dashed;
        color: var(--ink-secondary);
      }
      .skill-chip:hover {
        border-color: var(--accent);
      }
      .skill-chip__alias {
        color: var(--ink-tertiary);
        font-size: var(--text-xs);
      }
      .skill-chip__evidence {
        margin-top: var(--space-2);
      }
    `,
  ],
})
export class SkillChipComponent {
  @Input({ required: true }) rawText!: string;
  @Input() skill: SkillRef | null = null;
  @Input() evidence: Evidence | null = null;

  protected readonly expanded = signal(false);

  toggle(): void {
    if (this.evidence) {
      this.expanded.update((value) => !value);
    }
  }
}
