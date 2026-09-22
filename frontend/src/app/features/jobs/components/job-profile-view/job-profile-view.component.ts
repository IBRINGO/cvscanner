import { ChangeDetectionStrategy, Component, Input } from '@angular/core';
import { EvidenceNoteComponent } from '../../../../shared/components/ui/evidence-note/evidence-note.component';
import { JobProfile, JobRequirement } from '../../models/job-profile.model';

/**
 * Structured detail view for a job offer (section 47). Required and
 * preferred requirements are visually distinguished by weight (filled
 * vs outlined), never by color - there is no candidate to compare
 * against yet, so nothing here may look like a compatibility verdict.
 */
@Component({
  selector: 'app-job-profile-view',
  standalone: true,
  imports: [EvidenceNoteComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <article class="job-profile">
      <header class="job-profile__masthead">
        <h1>{{ profile.title ?? 'Untitled role' }}</h1>
        <p class="text-secondary">
          @if (profile.company) {
            <span>{{ profile.company }}</span>
          }
          @if (profile.location) {
            <span> | {{ profile.location }}</span>
          }
        </p>
        <p class="job-profile__tags">
          @if (profile.seniority) {
            <span class="job-profile__tag">{{ profile.seniority }}</span>
          }
          @if (profile.employment_type) {
            <span class="job-profile__tag">{{ profile.employment_type }}</span>
          }
        </p>
      </header>

      @if (profile.summary) {
        <section class="job-profile__section">
          <h2>Summary</h2>
          <p>{{ profile.summary }}</p>
        </section>
      }

      @if (profile.responsibilities.length > 0) {
        <section class="job-profile__section">
          <h2>Responsibilities</h2>
          <ul class="job-profile__list">
            @for (item of profile.responsibilities; track item) {
              <li>{{ item }}</li>
            }
          </ul>
        </section>
      }

      @if (requiredRequirements().length > 0) {
        <section class="job-profile__section">
          <h2>Required</h2>
          <ul class="job-profile__requirements">
            @for (requirement of requiredRequirements(); track $index) {
              <li>
                <span class="job-profile__requirement job-profile__requirement--required">
                  {{ requirement.skill?.canonical_name ?? requirement.raw_text }}
                </span>
                @if (requirement.evidence) {
                  <app-evidence-note [evidence]="requirement.evidence" />
                }
              </li>
            }
          </ul>
        </section>
      }

      @if (preferredRequirements().length > 0) {
        <section class="job-profile__section">
          <h2>Preferred</h2>
          <ul class="job-profile__requirements">
            @for (requirement of preferredRequirements(); track $index) {
              <li>
                <span class="job-profile__requirement job-profile__requirement--preferred">
                  {{ requirement.skill?.canonical_name ?? requirement.raw_text }}
                </span>
                @if (requirement.evidence) {
                  <app-evidence-note [evidence]="requirement.evidence" />
                }
              </li>
            }
          </ul>
        </section>
      }
    </article>
  `,
  styles: [
    `
      .job-profile {
        max-width: 720px;
        display: flex;
        flex-direction: column;
        gap: var(--space-6);
      }
      .job-profile__masthead {
        border-bottom: 1px solid var(--border-subtle);
        padding-bottom: var(--space-4);
        display: flex;
        flex-direction: column;
        gap: var(--space-2);
      }
      .job-profile__tags {
        display: flex;
        gap: var(--space-2);
      }
      .job-profile__tag {
        font-size: var(--text-xs);
        text-transform: uppercase;
        letter-spacing: 0.04em;
        color: var(--ink-tertiary);
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-sm);
        padding: 2px var(--space-2);
      }
      .job-profile__section h2 {
        margin-bottom: var(--space-3);
      }
      .job-profile__list {
        padding-left: var(--space-5);
        color: var(--ink-secondary);
        display: flex;
        flex-direction: column;
        gap: var(--space-2);
      }
      .job-profile__requirements {
        list-style: none;
        margin: 0;
        padding: 0;
        display: flex;
        flex-direction: column;
        gap: var(--space-3);
      }
      .job-profile__requirement {
        display: inline-block;
        padding: var(--space-1) var(--space-3);
        border-radius: var(--radius-sm);
        font-size: var(--text-sm);
      }
      .job-profile__requirement--required {
        background: var(--ink-primary);
        color: var(--surface-raised);
        font-weight: 500;
      }
      .job-profile__requirement--preferred {
        border: 1px solid var(--border-strong);
        color: var(--ink-primary);
      }
    `,
  ],
})
export class JobProfileViewComponent {
  @Input({ required: true }) profile!: JobProfile;

  requiredRequirements(): JobRequirement[] {
    return this.profile.requirements.filter((r) => r.importance === 'REQUIRED');
  }

  preferredRequirements(): JobRequirement[] {
    return this.profile.requirements.filter((r) => r.importance === 'PREFERRED');
  }
}
