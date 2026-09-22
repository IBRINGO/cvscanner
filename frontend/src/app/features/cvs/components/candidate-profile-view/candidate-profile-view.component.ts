import { ChangeDetectionStrategy, Component, Input } from '@angular/core';
import { NgIcon, provideIcons } from '@ng-icons/core';
import { CVSCANNER_ICONS } from '../../../../core/icons';
import { EntityTagComponent } from '../../../../shared/components/ui/entity-tag/entity-tag.component';
import { EvidenceNoteComponent } from '../../../../shared/components/ui/evidence-note/evidence-note.component';
import { SkillChipComponent } from '../../../../shared/components/ui/skill-chip/skill-chip.component';
import { formatEnumLabel } from '../../../../shared/utils/format-label';
import { CandidateProfile, CandidateSkill } from '../../models/candidate-profile.model';

interface SkillGroup {
  category: string;
  skills: CandidateSkill[];
}

/**
 * The structured intelligence view of a CV (section 44): an editorial
 * document layout, not a JSON dump. Each fact that carries evidence
 * exposes it inline (skill chips, timeline entries) rather than on a
 * separate "raw data" tab - see section 45.
 */
@Component({
  selector: 'app-candidate-profile-view',
  standalone: true,
  imports: [EvidenceNoteComponent, SkillChipComponent, EntityTagComponent, NgIcon],
  viewProviders: [provideIcons(CVSCANNER_ICONS)],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <article class="profile">
      <header class="profile__masthead">
        <h1>{{ profile.full_name ?? 'Unnamed candidate' }}</h1>
        <p class="profile__contact text-secondary">
          @for (item of contactItems(); track item; let last = $last) {
            <span>{{ item }}</span>
            @if (!last) {
              <span class="profile__divider" aria-hidden="true">|</span>
            }
          }
        </p>
      </header>

      @if (profile.summary) {
        <section class="profile__section">
          <h2><ng-icon name="lucideFileText" size="18" />Summary</h2>
          <p>{{ profile.summary }}</p>
        </section>
      }

      @if (profile.experiences.length > 0) {
        <section class="profile__section">
          <h2><ng-icon name="lucideBriefcase" size="18" />Experience</h2>
          <ul class="profile__timeline">
            @for (experience of profile.experiences; track $index) {
              <li class="profile__entry">
                <div class="profile__entry-head">
                  <span class="profile__entry-title">
                    {{ experience.title ?? 'Role' }}
                    @if (experience.company) {
                      <span class="text-secondary"> at {{ experience.company }}</span>
                    }
                  </span>
                  @if (experience.start_date_raw) {
                    <span class="profile__entry-dates font-mono text-tertiary">
                      {{ experience.start_date_raw }} - {{ experience.end_date_raw ?? 'Present' }}
                    </span>
                  }
                </div>
                @if (experience.seniority && experience.seniority !== 'UNKNOWN') {
                  <app-entity-tag [label]="formatEnumLabel(experience.seniority)" icon="lucideLayers" />
                }
                @if (experience.description) {
                  <p class="text-secondary">{{ experience.description }}</p>
                }
                @if (experience.achievements.length > 0) {
                  <ul class="profile__achievements">
                    @for (achievement of experience.achievements; track achievement) {
                      <li>{{ achievement }}</li>
                    }
                  </ul>
                }
                @if (experience.technologies.length > 0) {
                  <div class="profile__tech">
                    @for (tech of experience.technologies; track tech) {
                      <span class="profile__tech-chip font-mono">{{ tech }}</span>
                    }
                  </div>
                }
                @if (experience.evidence) {
                  <app-evidence-note [evidence]="experience.evidence" />
                }
              </li>
            }
          </ul>
        </section>
      }

      @if (profile.education.length > 0) {
        <section class="profile__section">
          <h2><ng-icon name="lucideGraduationCap" size="18" />Education</h2>
          <ul class="profile__timeline">
            @for (entry of profile.education; track $index) {
              <li class="profile__entry">
                <div class="profile__entry-head">
                  <span class="profile__entry-title">
                    {{ entry.degree ?? 'Program' }}
                    @if (entry.institution) {
                      <span class="text-secondary"> at {{ entry.institution }}</span>
                    }
                  </span>
                  @if (entry.start_date_raw) {
                    <span class="profile__entry-dates font-mono text-tertiary">
                      {{ entry.start_date_raw }} - {{ entry.end_date_raw ?? '' }}
                    </span>
                  }
                </div>
                @if (entry.degree_level && entry.degree_level !== 'UNKNOWN') {
                  <app-entity-tag [label]="formatEnumLabel(entry.degree_level)" icon="lucideGraduationCap" />
                }
                @if (entry.evidence) {
                  <app-evidence-note [evidence]="entry.evidence" />
                }
              </li>
            }
          </ul>
        </section>
      }

      @if (profile.skills.length > 0) {
        <section class="profile__section">
          <h2><ng-icon name="lucideCode" size="18" />Skills</h2>
          <div class="profile__skill-clusters">
            @for (group of skillGroups(); track group.category) {
              <div class="profile__skill-group">
                <h3 class="profile__skill-category text-tertiary">{{ formatEnumLabel(group.category) }}</h3>
                <div class="profile__skill-chips">
                  @for (mention of group.skills; track mention.raw_text) {
                    <app-skill-chip
                      [rawText]="mention.raw_text"
                      [skill]="mention.skill"
                      [evidence]="mention.evidence"
                    />
                  }
                </div>
              </div>
            }
          </div>
        </section>
      }

      @if (profile.projects.length > 0) {
        <section class="profile__section">
          <h2><ng-icon name="lucideFolder" size="18" />Projects</h2>
          <ul class="profile__timeline">
            @for (project of profile.projects; track project.name) {
              <li class="profile__entry">
                <span class="profile__entry-title">{{ project.name }}</span>
                @if (project.description) {
                  <p class="text-secondary">{{ project.description }}</p>
                }
                @if (project.technologies.length > 0) {
                  <div class="profile__tech">
                    @for (tech of project.technologies; track tech) {
                      <span class="profile__tech-chip font-mono">{{ tech }}</span>
                    }
                  </div>
                }
              </li>
            }
          </ul>
        </section>
      }

      @if (profile.certifications.length > 0) {
        <section class="profile__section">
          <h2><ng-icon name="lucideAward" size="18" />Certifications</h2>
          <ul class="profile__timeline">
            @for (cert of profile.certifications; track cert.name) {
              <li class="profile__entry">
                <span class="profile__entry-title">{{ cert.name }}</span>
                @if (cert.issuer) {
                  <span class="text-secondary"> - {{ cert.issuer }}</span>
                }
                @if (cert.date_raw) {
                  <span class="font-mono text-tertiary"> ({{ cert.date_raw }})</span>
                }
              </li>
            }
          </ul>
        </section>
      }

      @if (profile.languages.length > 0) {
        <section class="profile__section">
          <h2><ng-icon name="lucideLanguages" size="18" />Languages</h2>
          <div class="profile__language-list">
            @for (language of profile.languages; track language.name) {
              <div class="profile__language">
                <span class="profile__entry-title">{{ language.canonical_name ?? language.name }}</span>
                @if (language.proficiency_normalized && language.proficiency_normalized !== 'UNKNOWN') {
                  <app-entity-tag [label]="formatEnumLabel(language.proficiency_normalized)" icon="lucideGlobe" />
                } @else if (language.proficiency) {
                  <span class="text-tertiary">({{ language.proficiency }})</span>
                }
              </div>
            }
          </div>
        </section>
      }
    </article>
  `,
  styles: [
    `
      .profile {
        max-width: 720px;
        display: flex;
        flex-direction: column;
        gap: var(--space-6);
      }
      .profile__masthead {
        border-bottom: 1px solid var(--border-subtle);
        padding-bottom: var(--space-4);
      }
      .profile__contact {
        margin-top: var(--space-2);
        display: flex;
        gap: var(--space-2);
        flex-wrap: wrap;
      }
      .profile__divider {
        color: var(--border-strong);
      }
      .profile__section h2 {
        margin-bottom: var(--space-3);
        display: flex;
        align-items: center;
        gap: var(--space-2);
      }
      .profile__language-list {
        display: flex;
        flex-direction: column;
        gap: var(--space-2);
      }
      .profile__language {
        display: flex;
        align-items: center;
        gap: var(--space-2);
      }
      .profile__timeline {
        list-style: none;
        margin: 0;
        padding: 0;
        display: flex;
        flex-direction: column;
        gap: var(--space-4);
      }
      .profile__entry {
        padding-left: var(--space-4);
        border-left: 2px solid var(--border-subtle);
        display: flex;
        flex-direction: column;
        gap: var(--space-2);
      }
      .profile__entry-head {
        display: flex;
        flex-wrap: wrap;
        justify-content: space-between;
        gap: var(--space-2);
      }
      .profile__entry-title {
        font-weight: 500;
        color: var(--ink-primary);
      }
      .profile__achievements {
        margin: 0;
        padding-left: var(--space-5);
        color: var(--ink-secondary);
        font-size: var(--text-sm);
      }
      .profile__tech {
        display: flex;
        flex-wrap: wrap;
        gap: var(--space-2);
      }
      .profile__tech-chip {
        font-size: var(--text-xs);
        color: var(--ink-secondary);
        background: var(--surface-sunken);
        padding: 2px var(--space-2);
        border-radius: var(--radius-sm);
      }
      .profile__skill-clusters {
        display: flex;
        flex-direction: column;
        gap: var(--space-4);
      }
      .profile__skill-category {
        text-transform: uppercase;
        letter-spacing: 0.06em;
        font-size: var(--text-xs);
        margin-bottom: var(--space-2);
      }
      .profile__skill-chips {
        display: flex;
        flex-wrap: wrap;
        gap: var(--space-2);
      }
    `,
  ],
})
export class CandidateProfileViewComponent {
  @Input({ required: true }) profile!: CandidateProfile;

  contactItems(): string[] {
    const items: string[] = [];
    if (this.profile.email) items.push(this.profile.email);
    if (this.profile.phone) items.push(this.profile.phone);
    if (this.profile.location) items.push(this.profile.location);
    return items;
  }

  formatEnumLabel(value: string | null | undefined): string {
    return formatEnumLabel(value);
  }

  skillGroups(): SkillGroup[] {
    const groups = new Map<string, CandidateSkill[]>();
    for (const mention of this.profile.skills) {
      const category = mention.skill?.category ?? 'Uncategorized';
      const list = groups.get(category) ?? [];
      list.push(mention);
      groups.set(category, list);
    }
    return Array.from(groups.entries()).map(([category, skills]) => ({ category, skills }));
  }
}
