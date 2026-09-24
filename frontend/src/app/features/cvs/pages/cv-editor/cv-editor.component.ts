import { CdkDrag, CdkDragDrop, CdkDragHandle, CdkDropList, moveItemInArray } from '@angular/cdk/drag-drop';
import { ChangeDetectionStrategy, Component, OnInit, computed, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { NgIcon, provideIcons } from '@ng-icons/core';
import { CVSCANNER_ICONS } from '../../../../core/icons';
import { ApplicationSessionService } from '../../../applications/services/application-session.service';
import {
  CvDocumentRendererComponent,
  PERSONAL_INFO_ID,
} from '../../../templates/components/cv-document-renderer/cv-document-renderer.component';
import { CV_TEMPLATES, TemplateDefinition, findTemplate } from '../../../templates/models/template-definition.model';
import { CandidateProfile, Education, Experience, Project } from '../../models/candidate-profile.model';
import {
  CustomSectionRef,
  CvSectionRef,
  DEFAULT_SECTION_ORDER,
  SECTION_LABELS,
} from '../../models/cv-document.model';
import { EditorSnapshot } from '../../models/editor-state.model';
import { applyTailoringChanges } from '../../utils/apply-tailoring-changes';
import { CvApiService, RenderPdfRequest } from '../../services/cv-api.service';
import { TailoringApiService } from '../../../tailoring/services/tailoring-api.service';

/** Reference width the renderer is measured at before being scaled into
 * a template-bar thumbnail - must match `.cv-page`'s max-width. */
const THUMB_REFERENCE_WIDTH = 760;
const THUMB_WIDTH = 74;
const THUMB_SCALE = THUMB_WIDTH / THUMB_REFERENCE_WIDTH;

/**
 * The CV editor: structured editing over the same CandidateProfile the
 * rest of the product already trusts, rendered live through the same
 * CvDocumentRenderer templates will use for export. Deliberately
 * client-side only - edits here never call a backend endpoint that
 * would let free-text bypass the Truth Layer's claim validation
 * (see docs/architecture/phase-6-frontend-redesign.md). Reordering,
 * hiding, and rewording existing text is always safe because it is the
 * candidate's own hand-typed edit, not an AI-generated claim.
 *
 * Full-screen: routed outside MainLayoutComponent (see app.routes.ts)
 * so the document gets the entire viewport instead of sharing it with
 * the app's sidebar/header - the editor supplies its own compact
 * topbar and back link instead.
 */
@Component({
  selector: 'app-cv-editor-page',
  standalone: true,
  imports: [RouterLink, FormsModule, NgIcon, CvDocumentRendererComponent, CdkDropList, CdkDrag, CdkDragHandle],
  viewProviders: [provideIcons(CVSCANNER_ICONS)],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="editor-shell">
      <div class="editor__topbar">
        <a [routerLink]="['/cvs', documentId]" class="editor__back">
          <ng-icon name="lucideArrowLeft" size="15" />
          Back to CV
        </a>
        @if (profile()) {
          <button type="button" class="editor__export-trigger" (click)="openExport()">
            <ng-icon name="lucideFileCheck" size="15" />
            Download PDF
          </button>
        }
      </div>

      @if (showExport()) {
        <div class="editor__export-overlay" role="dialog" aria-label="Export your CV">
          <div class="editor__export-card">
            <h2>Your CV is ready</h2>
            <dl class="editor__export-facts">
              <div>
                <dt>Template</dt>
                <dd>{{ currentTemplate().name }}</dd>
              </div>
              <div>
                <dt>Length</dt>
                <dd>~{{ estimatedPages() }} page{{ estimatedPages() === 1 ? '' : 's' }}</dd>
              </div>
              <div>
                <dt>Format</dt>
                <dd><ng-icon name="lucideFileCheck" size="14" /> A4 PDF</dd>
              </div>
            </dl>
            <div class="editor__export-actions">
              <button type="button" class="editor__export-download" [disabled]="downloading()" (click)="downloadPdf()">
                <ng-icon name="lucideDownload" size="16" />
                {{ downloading() ? 'Preparing your PDF...' : 'Download PDF' }}
              </button>
              <button type="button" class="editor__export-cancel" (click)="closeExport()">Continue editing</button>
            </div>
            @if (downloadError()) {
              <p class="editor__export-error">{{ downloadError() }}</p>
            }
            <p class="text-tertiary editor__export-note">
              Rendered server-side at A4 size so the download matches your template exactly.
            </p>
          </div>
        </div>
      }

      @if (showPreview() && profile()) {
        <div class="editor__preview-modal-overlay" role="dialog" aria-label="CV preview">
          <div class="editor__preview-modal">
            <div class="editor__preview-modal-topbar">
              <span class="editor__preview-modal-title">
                <ng-icon name="lucideEye" size="15" />
                Preview - {{ currentTemplate().name }}
              </span>
              <button type="button" class="editor__preview-modal-close" title="Close preview" (click)="closePreview()">
                <ng-icon name="lucideX" size="16" />
              </button>
            </div>
            <div class="editor__preview-modal-body">
              <app-cv-document-renderer
                [profile]="profile()!"
                [sectionOrder]="sectionOrder()"
                [hiddenSectionIds]="hiddenSectionIds()"
                [template]="currentTemplate()"
                [groupSkillsByCategory]="groupSkillsByCategory()"
              />
            </div>
          </div>
        </div>
      }

      @if (loading()) {
        <p class="text-secondary editor__loading">Loading your CV...</p>
      } @else if (!profile()) {
        <p class="text-secondary editor__loading">This CV has no extracted profile yet.</p>
      } @else {
        @if (fromTailoringId() && showTailoredBanner()) {
          <div class="editor__tailored-banner">
            <ng-icon name="lucideCircleCheck" size="15" />
            Editing your tailored CV - accepted, factually-verified changes are already applied.
          </div>
        }

        <div class="editor-template-bar">
          <span class="editor-template-bar__label">Template</span>
          <div class="editor-template-bar__scroll">
            @for (t of templates; track t.id) {
              <button
                type="button"
                class="editor-template-chip"
                [attr.data-active]="templateId() === t.id"
                (click)="setTemplate(t.id)"
                [title]="t.name"
              >
                <span class="editor-template-chip__thumb">
                  <span class="editor-template-chip__canvas">
                    <app-cv-document-renderer
                      [profile]="profile()!"
                      [sectionOrder]="sectionOrder()"
                      [template]="t"
                      [groupSkillsByCategory]="groupSkillsByCategory()"
                    />
                  </span>
                </span>
                <span class="editor-template-chip__name">{{ t.name }}</span>
              </button>
            }
          </div>
          <a routerLink="/templates" class="editor__gallery-link">Browse all templates</a>
        </div>

        <div class="editor">
          <aside class="editor__panel editor__sections">
            <button
              type="button"
              class="editor__rail-btn"
              title="Personal info"
              [attr.data-selected]="selectedSectionId() === personalInfoId"
              (click)="selectedSectionId.set(personalInfoId)"
            >
              <ng-icon name="lucideUserRound" size="18" />
            </button>

            <div class="editor__sections-menu">
              <button
                type="button"
                class="editor__rail-btn"
                title="Sections"
                [attr.aria-expanded]="sectionsMenuOpen()"
                (click)="toggleSectionsMenu()"
              >
                <ng-icon name="lucideLayers" size="18" />
              </button>

              @if (sectionsMenuOpen()) {
                <div class="editor__section-menu-backdrop" (click)="closeSectionsMenu()"></div>
                <div class="editor__sections-dropdown">
                  <p class="editor__hint text-tertiary">Drag to reorder</p>
                  <ul class="editor__section-list" cdkDropList (cdkDropListDropped)="onSectionDrop($event)">
                    @for (ref of sectionOrder(); track ref.id; let i = $index) {
                      <li
                        class="editor__section-row"
                        cdkDrag
                        [attr.data-selected]="selectedSectionId() === ref.id"
                        [attr.data-hidden]="hiddenSectionIds().includes(ref.id)"
                      >
                        <span class="editor__drag-handle" cdkDragHandle>
                          <ng-icon name="lucideGripVertical" size="14" />
                        </span>
                        <button type="button" class="editor__section-name" (click)="selectSectionAndClose(ref.id)">
                          {{ labelFor(ref) }}
                        </button>
                        <div class="editor__section-actions">
                          <button
                            type="button"
                            [title]="hiddenSectionIds().includes(ref.id) ? 'Show section' : 'Hide section'"
                            (click)="toggleHiddenAndClose(ref.id)"
                          >
                            <ng-icon [name]="hiddenSectionIds().includes(ref.id) ? 'lucideCircleX' : 'lucideCircleCheck'" size="13" />
                          </button>
                        </div>
                      </li>
                    }
                  </ul>
                  <button type="button" class="editor__add-section" (click)="addCustomSection()">
                    <ng-icon name="lucideFolder" size="14" />
                    Add custom section
                  </button>
                </div>
              }
            </div>

            <div class="editor__export-group">
              <button type="button" class="editor__rail-btn" title="Preview" (click)="openPreview()">
                <ng-icon name="lucideEye" size="18" />
              </button>
              <button type="button" class="editor__rail-btn" title="Download PDF" (click)="openExport()">
                <ng-icon name="lucideDownload" size="18" />
              </button>
            </div>

            <div class="editor__history">
              <button type="button" class="editor__rail-btn" title="Undo" [disabled]="!canUndo()" (click)="undo()">
                <ng-icon name="lucideUndo2" size="18" />
              </button>
              <button type="button" class="editor__rail-btn" title="Redo" [disabled]="!canRedo()" (click)="redo()">
                <ng-icon name="lucideRedo2" size="18" />
              </button>
            </div>
          </aside>

          <div class="editor__preview">
            <app-cv-document-renderer
              [profile]="profile()!"
              [sectionOrder]="sectionOrder()"
              [hiddenSectionIds]="hiddenSectionIds()"
              [template]="currentTemplate()"
              [interactive]="true"
              [selectedSectionId]="selectedSectionId()"
              [groupSkillsByCategory]="groupSkillsByCategory()"
              (sectionSelected)="selectedSectionId.set($event)"
            />
          </div>

          <aside class="editor__panel editor__properties">
            @if (selectedSectionId() === personalInfoId) {
              <h2>Personal info</h2>
              <label class="editor__field">
                <span class="editor__label">Full name</span>
                <input type="text" [ngModel]="profile()!.full_name ?? ''" (ngModelChange)="updatePersonalInfo('full_name', $event)" />
              </label>
              <label class="editor__field">
                <span class="editor__label">Email</span>
                <input type="text" [ngModel]="profile()!.email ?? ''" (ngModelChange)="updatePersonalInfo('email', $event)" />
              </label>
              <label class="editor__field">
                <span class="editor__label">Phone</span>
                <input type="text" [ngModel]="profile()!.phone ?? ''" (ngModelChange)="updatePersonalInfo('phone', $event)" />
              </label>
              <label class="editor__field">
                <span class="editor__label">Location</span>
                <input type="text" [ngModel]="profile()!.location ?? ''" (ngModelChange)="updatePersonalInfo('location', $event)" />
              </label>

              <div class="editor__field">
                <span class="editor__label">Links</span>
                <ul class="editor__chip-list">
                  @for (link of profile()!.links; track $index; let i = $index) {
                    <li>
                      {{ link }}
                      <button type="button" title="Remove" (click)="removeLink(i)">
                        <ng-icon name="lucideX" size="12" />
                      </button>
                    </li>
                  }
                </ul>
                <div class="editor__add-row">
                  <input #newLink type="text" placeholder="e.g. linkedin.com/in/you" (keydown.enter)="addLink(newLink.value); newLink.value = ''" />
                  <button type="button" (click)="addLink(newLink.value); newLink.value = ''">
                    <ng-icon name="lucidePlus" size="14" />
                  </button>
                </div>
              </div>
            } @else {
              <h2>{{ labelFor(selectedRef()) }}</h2>

              @switch (selectedRef()?.kind) {
                @case ('summary') {
                  <label class="editor__field">
                    <span class="editor__label">Summary</span>
                    <textarea
                      rows="6"
                      [ngModel]="profile()!.summary ?? ''"
                      (ngModelChange)="updateSummary($event)"
                    ></textarea>
                  </label>
                }
                @case ('experience') {
                  <p class="editor__hint text-tertiary">Drag to reorder by relevance to the job you're targeting</p>
                  <div cdkDropList (cdkDropListDropped)="onExperienceDrop($event)">
                    @for (exp of profile()!.experiences; track $index; let i = $index) {
                      <div class="editor__entry-card" cdkDrag>
                        <div class="editor__entry-toolbar">
                          <span class="editor__drag-handle" cdkDragHandle>
                            <ng-icon name="lucideGripVertical" size="14" />
                          </span>
                          <span class="editor__entry-spacer"></span>
                          <button type="button" title="Duplicate" (click)="duplicateExperience(i)">
                            <ng-icon name="lucideCopy" size="13" />
                          </button>
                          <button type="button" title="Delete" (click)="removeExperience(i)">
                            <ng-icon name="lucideTrash2" size="13" />
                          </button>
                        </div>
                        <label class="editor__field">
                          <span class="editor__label">Role</span>
                          <input type="text" [ngModel]="exp.title ?? ''" (ngModelChange)="updateExperience(i, 'title', $event)" />
                        </label>
                        <label class="editor__field">
                          <span class="editor__label">Company</span>
                          <input type="text" [ngModel]="exp.company ?? ''" (ngModelChange)="updateExperience(i, 'company', $event)" />
                        </label>
                        <div class="editor__field-row">
                          <label class="editor__field">
                            <span class="editor__label">Start date</span>
                            <input
                              type="text"
                              placeholder="e.g. Jan 2020"
                              [ngModel]="exp.start_date_raw ?? ''"
                              (ngModelChange)="updateExperience(i, 'start_date_raw', $event)"
                            />
                          </label>
                          <label class="editor__field">
                            <span class="editor__label">End date</span>
                            <input
                              type="text"
                              placeholder="e.g. Present"
                              [ngModel]="exp.end_date_raw ?? ''"
                              (ngModelChange)="updateExperience(i, 'end_date_raw', $event)"
                            />
                          </label>
                        </div>
                        <label class="editor__field">
                          <span class="editor__label">Description</span>
                          <textarea rows="3" [ngModel]="exp.description ?? ''" (ngModelChange)="updateExperience(i, 'description', $event)"></textarea>
                        </label>
                      </div>
                    }
                  </div>
                  <button type="button" class="editor__add-entry" (click)="addExperience()">
                    <ng-icon name="lucidePlus" size="14" />
                    Add experience
                  </button>
                }
                @case ('education') {
                  @for (entry of profile()!.education; track $index; let i = $index) {
                    <div class="editor__entry-card">
                      <div class="editor__entry-toolbar">
                        <button type="button" title="Duplicate" (click)="duplicateEducation(i)">
                          <ng-icon name="lucideCopy" size="13" />
                        </button>
                        <button type="button" title="Delete" (click)="removeEducation(i)">
                          <ng-icon name="lucideTrash2" size="13" />
                        </button>
                      </div>
                      <label class="editor__field">
                        <span class="editor__label">Degree</span>
                        <input type="text" [ngModel]="entry.degree ?? ''" (ngModelChange)="updateEducation(i, 'degree', $event)" />
                      </label>
                      <label class="editor__field">
                        <span class="editor__label">Institution</span>
                        <input type="text" [ngModel]="entry.institution ?? ''" (ngModelChange)="updateEducation(i, 'institution', $event)" />
                      </label>
                      <div class="editor__field-row">
                        <label class="editor__field">
                          <span class="editor__label">Start date</span>
                          <input
                            type="text"
                            placeholder="e.g. 2013"
                            [ngModel]="entry.start_date_raw ?? ''"
                            (ngModelChange)="updateEducation(i, 'start_date_raw', $event)"
                          />
                        </label>
                        <label class="editor__field">
                          <span class="editor__label">End date</span>
                          <input
                            type="text"
                            placeholder="e.g. 2017"
                            [ngModel]="entry.end_date_raw ?? ''"
                            (ngModelChange)="updateEducation(i, 'end_date_raw', $event)"
                          />
                        </label>
                      </div>
                    </div>
                  }
                  <button type="button" class="editor__add-entry" (click)="addEducation()">
                    <ng-icon name="lucidePlus" size="14" />
                    Add education
                  </button>
                }
                @case ('projects') {
                  <p class="editor__hint text-tertiary">Drag to reorder by relevance to the job you're targeting</p>
                  <div cdkDropList (cdkDropListDropped)="onProjectDrop($event)">
                    @for (project of profile()!.projects; track $index; let i = $index) {
                      <div class="editor__entry-card" cdkDrag>
                        <div class="editor__entry-toolbar">
                          <span class="editor__drag-handle" cdkDragHandle>
                            <ng-icon name="lucideGripVertical" size="14" />
                          </span>
                          <span class="editor__entry-spacer"></span>
                          <button type="button" title="Duplicate" (click)="duplicateProject(i)">
                            <ng-icon name="lucideCopy" size="13" />
                          </button>
                          <button type="button" title="Delete" (click)="removeListItem('projects', i)">
                            <ng-icon name="lucideTrash2" size="13" />
                          </button>
                        </div>
                        <label class="editor__field">
                          <span class="editor__label">Title</span>
                          <input type="text" [ngModel]="project.name" (ngModelChange)="updateProject(i, 'name', $event)" />
                        </label>
                        <label class="editor__field">
                          <span class="editor__label">Description</span>
                          <textarea rows="3" [ngModel]="project.description ?? ''" (ngModelChange)="updateProject(i, 'description', $event)"></textarea>
                        </label>
                      </div>
                    }
                  </div>
                  <button type="button" class="editor__add-entry" (click)="addProject()">
                    <ng-icon name="lucidePlus" size="14" />
                    Add project
                  </button>
                }
                @case ('skills') {
                  <label class="editor__toggle-row">
                    <input
                      type="checkbox"
                      [ngModel]="groupSkillsByCategory()"
                      (ngModelChange)="groupSkillsByCategory.set($event)"
                    />
                    <span>Group by category</span>
                  </label>
                  <p class="editor__hint text-tertiary">
                    Optional - works best on two-column templates (Modern Split, Technical).
                  </p>

                  <ul class="editor__skill-list">
                    @for (skill of profile()!.skills; track $index; let i = $index) {
                      <li class="editor__skill-row">
                        <span class="editor__skill-name">{{ skill.skill?.canonical_name ?? skill.raw_text }}</span>
                        @if (groupSkillsByCategory()) {
                          <input
                            type="text"
                            class="editor__skill-category"
                            placeholder="Category"
                            [ngModel]="skill.skill?.category ?? ''"
                            (ngModelChange)="updateSkillCategory(i, $event)"
                          />
                        }
                        <button type="button" title="Remove from CV" (click)="removeListItem('skills', i)">
                          <ng-icon name="lucideX" size="12" />
                        </button>
                      </li>
                    }
                  </ul>
                  <div class="editor__add-row">
                    <input #newSkill type="text" placeholder="Add a skill" (keydown.enter)="addSkill(newSkill.value); newSkill.value = ''" />
                    <button type="button" (click)="addSkill(newSkill.value); newSkill.value = ''">
                      <ng-icon name="lucidePlus" size="14" />
                    </button>
                  </div>
                }
                @case ('certifications') {
                  <ul class="editor__chip-list">
                    @for (cert of profile()!.certifications; track $index; let i = $index) {
                      <li>
                        {{ cert.name }}
                        <button type="button" title="Remove from CV" (click)="removeListItem('certifications', i)">
                          <ng-icon name="lucideX" size="12" />
                        </button>
                      </li>
                    }
                  </ul>
                  <div class="editor__add-row">
                    <input #newCert type="text" placeholder="Add a certification" (keydown.enter)="addCertification(newCert.value); newCert.value = ''" />
                    <button type="button" (click)="addCertification(newCert.value); newCert.value = ''">
                      <ng-icon name="lucidePlus" size="14" />
                    </button>
                  </div>
                }
                @case ('languages') {
                  <ul class="editor__chip-list">
                    @for (lang of profile()!.languages; track $index; let i = $index) {
                      <li>
                        {{ lang.canonical_name ?? lang.name }}
                        <button type="button" title="Remove from CV" (click)="removeListItem('languages', i)">
                          <ng-icon name="lucideX" size="12" />
                        </button>
                      </li>
                    }
                  </ul>
                  <div class="editor__add-row">
                    <input #newLang type="text" placeholder="Add a language" (keydown.enter)="addLanguage(newLang.value); newLang.value = ''" />
                    <button type="button" (click)="addLanguage(newLang.value); newLang.value = ''">
                      <ng-icon name="lucidePlus" size="14" />
                    </button>
                  </div>
                }
                @case ('custom') {
                  <label class="editor__field">
                    <span class="editor__label">Section title</span>
                    <input type="text" [ngModel]="selectedCustomTitle()" (ngModelChange)="updateCustomSection('title', $event)" />
                  </label>
                  <label class="editor__field">
                    <span class="editor__label">Content</span>
                    <textarea rows="6" [ngModel]="selectedCustomContent()" (ngModelChange)="updateCustomSection('content', $event)"></textarea>
                  </label>
                  <button type="button" class="editor__remove-section" (click)="removeCustomSection()">
                    Remove this section
                  </button>
                }
              }
            }
          </aside>
        </div>
      }
    </div>
  `,
  styleUrl: './cv-editor.component.scss',
})
export class CvEditorComponent implements OnInit {
  // Public (not protected): the editor's mutation methods and state are
  // exercised directly in tests, matching this codebase's convention for
  // components whose behavior is more than template-display state.
  readonly documentId: string;
  readonly loading = signal(true);
  readonly profile = signal<CandidateProfile | null>(null);
  readonly sectionOrder = signal<CvSectionRef[]>(DEFAULT_SECTION_ORDER);
  readonly hiddenSectionIds = signal<string[]>([]);
  readonly templateId = signal('ats-classic');
  readonly selectedSectionId = signal<string>('summary');
  readonly templates = CV_TEMPLATES;
  readonly personalInfoId = PERSONAL_INFO_ID;
  readonly sectionsMenuOpen = signal(false);
  /** Optional per section 67 of this pass's brief - off by default
   * everywhere, never assumed on just because a 2-column template is
   * active (the candidate decides, from the Skills panel). */
  readonly groupSkillsByCategory = signal(false);
  protected readonly THUMB_WIDTH = THUMB_WIDTH;
  protected readonly THUMB_SCALE = THUMB_SCALE;
  protected readonly THUMB_REFERENCE_WIDTH = THUMB_REFERENCE_WIDTH;

  private readonly past = signal<EditorSnapshot[]>([]);
  private readonly future = signal<EditorSnapshot[]>([]);
  readonly canUndo = computed(() => this.past().length > 0);
  readonly canRedo = computed(() => this.future().length > 0);

  readonly showExport = signal(false);
  readonly showPreview = signal(false);
  readonly estimatedPages = signal(1);
  readonly fromTailoringId = signal<string | null>(null);
  /** The tailored-CV banner is informational, not an ongoing status - it
   * self-dismisses a few seconds after load (see loadTailoredProfile())
   * instead of permanently occupying space at the top of the editor. */
  readonly showTailoredBanner = signal(true);
  readonly downloading = signal(false);
  readonly downloadError = signal<string | null>(null);

  protected readonly currentTemplate = computed<TemplateDefinition>(() => findTemplate(this.templateId()));
  protected readonly selectedRef = computed<CvSectionRef | undefined>(() =>
    this.sectionOrder().find((ref) => ref.id === this.selectedSectionId()),
  );

  private readonly route = inject(ActivatedRoute);
  private readonly session = inject(ApplicationSessionService);

  constructor(
    private readonly cvApi: CvApiService,
    private readonly tailoringApi: TailoringApiService,
  ) {
    this.documentId = this.route.snapshot.paramMap.get('id') ?? '';
  }

  setTemplate(id: string): void {
    this.templateId.set(id);
    this.session.setTemplate(id);
  }

  ngOnInit(): void {
    const requestedTemplate = this.route.snapshot.queryParamMap.get('template');
    if (requestedTemplate && this.templates.some((t) => t.id === requestedTemplate)) {
      this.setTemplate(requestedTemplate);
    }

    if (!this.documentId) {
      this.loading.set(false);
      return;
    }

    const tailoringId = this.route.snapshot.queryParamMap.get('tailoringId');

    this.cvApi.getProfile(this.documentId).subscribe({
      next: (response) => {
        if (!response.profile) {
          this.loading.set(false);
          return;
        }
        if (tailoringId) {
          this.loadTailoredProfile(tailoringId, response.profile);
        } else {
          this.profile.set(response.profile);
          this.loading.set(false);
        }
      },
      error: () => this.loading.set(false),
    });
  }

  private loadTailoredProfile(tailoringId: string, original: CandidateProfile): void {
    this.tailoringApi.getPlan(tailoringId).subscribe({
      next: (plan) => {
        this.profile.set(applyTailoringChanges(original, plan.changes));
        this.fromTailoringId.set(tailoringId);
        this.loading.set(false);
        setTimeout(() => this.showTailoredBanner.set(false), 6000);
      },
      error: () => {
        // The tailoring plan could not be loaded - fall back to the real
        // original profile rather than blocking the editor entirely.
        this.profile.set(original);
        this.loading.set(false);
      },
    });
  }

  labelFor(ref: CvSectionRef | undefined): string {
    if (!ref) return '';
    return ref.kind === 'custom' ? ref.title : (SECTION_LABELS[ref.kind] ?? ref.kind);
  }

  selectedCustomTitle(): string {
    const ref = this.selectedRef();
    return ref?.kind === 'custom' ? ref.title : '';
  }

  selectedCustomContent(): string {
    const ref = this.selectedRef();
    return ref?.kind === 'custom' ? ref.content : '';
  }

  onSectionDrop(event: CdkDragDrop<CvSectionRef[]>): void {
    if (event.previousIndex === event.currentIndex) return;
    this.pushHistory();
    const next = [...this.sectionOrder()];
    moveItemInArray(next, event.previousIndex, event.currentIndex);
    this.sectionOrder.set(next);
  }

  onExperienceDrop(event: CdkDragDrop<Experience[]>): void {
    if (event.previousIndex === event.currentIndex) return;
    this.pushHistory();
    this.profile.update((p) => {
      if (!p) return p;
      const experiences = [...p.experiences];
      moveItemInArray(experiences, event.previousIndex, event.currentIndex);
      return { ...p, experiences };
    });
  }

  onProjectDrop(event: CdkDragDrop<Project[]>): void {
    if (event.previousIndex === event.currentIndex) return;
    this.pushHistory();
    this.profile.update((p) => {
      if (!p) return p;
      const projects = [...p.projects];
      moveItemInArray(projects, event.previousIndex, event.currentIndex);
      return { ...p, projects };
    });
  }

  toggleHidden(id: string): void {
    this.pushHistory();
    this.hiddenSectionIds.update((ids) => (ids.includes(id) ? ids.filter((i) => i !== id) : [...ids, id]));
  }

  toggleSectionsMenu(): void {
    this.sectionsMenuOpen.update((open) => !open);
  }

  closeSectionsMenu(): void {
    this.sectionsMenuOpen.set(false);
  }

  selectSectionAndClose(id: string): void {
    this.selectedSectionId.set(id);
    this.closeSectionsMenu();
  }

  toggleHiddenAndClose(id: string): void {
    this.toggleHidden(id);
    this.closeSectionsMenu();
  }

  addCustomSection(): void {
    this.pushHistory();
    const id = `custom-${Date.now()}`;
    const section: CustomSectionRef = { id, kind: 'custom', title: 'New section', content: '' };
    this.sectionOrder.update((order) => [...order, section]);
    this.selectedSectionId.set(id);
    this.closeSectionsMenu();
  }

  removeCustomSection(): void {
    const ref = this.selectedRef();
    if (!ref || ref.kind !== 'custom') return;
    this.pushHistory();
    this.sectionOrder.update((order) => order.filter((r) => r.id !== ref.id));
    this.selectedSectionId.set('summary');
  }

  updateCustomSection(field: 'title' | 'content', value: string): void {
    const ref = this.selectedRef();
    if (!ref || ref.kind !== 'custom') return;
    this.pushHistory();
    this.sectionOrder.update((order) =>
      order.map((r) => (r.id === ref.id && r.kind === 'custom' ? { ...r, [field]: value } : r)),
    );
  }

  updatePersonalInfo(field: 'full_name' | 'email' | 'phone' | 'location', value: string): void {
    this.pushHistory();
    this.profile.update((p) => (p ? { ...p, [field]: value } : p));
  }

  addLink(value: string): void {
    const trimmed = value.trim();
    if (!trimmed) return;
    this.pushHistory();
    this.profile.update((p) => (p ? { ...p, links: [...p.links, trimmed] } : p));
  }

  removeLink(index: number): void {
    this.pushHistory();
    this.profile.update((p) => (p ? { ...p, links: p.links.filter((_, i) => i !== index) } : p));
  }

  updateSummary(value: string): void {
    this.pushHistory();
    this.profile.update((p) => (p ? { ...p, summary: value } : p));
  }

  updateExperience(
    index: number,
    field: keyof Pick<Experience, 'title' | 'company' | 'description' | 'start_date_raw' | 'end_date_raw'>,
    value: string,
  ): void {
    this.pushHistory();
    this.profile.update((p) => {
      if (!p) return p;
      const experiences = [...p.experiences];
      experiences[index] = { ...experiences[index], [field]: value };
      return { ...p, experiences };
    });
  }

  updateEducation(index: number, field: 'degree' | 'institution' | 'start_date_raw' | 'end_date_raw', value: string): void {
    this.pushHistory();
    this.profile.update((p) => {
      if (!p) return p;
      const education = [...p.education];
      education[index] = { ...education[index], [field]: value };
      return { ...p, education };
    });
  }

  addExperience(): void {
    this.pushHistory();
    const blank: Experience = {
      title: 'New role',
      company: null,
      start_date_raw: null,
      end_date_raw: null,
      description: '',
      achievements: [],
      technologies: [],
      seniority: null,
      evidence: null,
    };
    this.profile.update((p) => (p ? { ...p, experiences: [...p.experiences, blank] } : p));
  }

  duplicateExperience(index: number): void {
    this.pushHistory();
    this.profile.update((p) => {
      if (!p) return p;
      const experiences = [...p.experiences];
      experiences.splice(index + 1, 0, { ...experiences[index] });
      return { ...p, experiences };
    });
  }

  removeExperience(index: number): void {
    this.pushHistory();
    this.profile.update((p) => (p ? { ...p, experiences: p.experiences.filter((_, i) => i !== index) } : p));
  }

  addEducation(): void {
    this.pushHistory();
    const blank: Education = {
      institution: 'New institution',
      degree: null,
      field_of_study: null,
      start_date_raw: null,
      end_date_raw: null,
      degree_level: null,
      evidence: null,
    };
    this.profile.update((p) => (p ? { ...p, education: [...p.education, blank] } : p));
  }

  duplicateEducation(index: number): void {
    this.pushHistory();
    this.profile.update((p) => {
      if (!p) return p;
      const education = [...p.education];
      education.splice(index + 1, 0, { ...education[index] });
      return { ...p, education };
    });
  }

  removeEducation(index: number): void {
    this.pushHistory();
    this.profile.update((p) => (p ? { ...p, education: p.education.filter((_, i) => i !== index) } : p));
  }

  addProject(): void {
    this.pushHistory();
    const blank: Project = { name: 'New project', description: '', technologies: [] };
    this.profile.update((p) => (p ? { ...p, projects: [...p.projects, blank] } : p));
  }

  duplicateProject(index: number): void {
    this.pushHistory();
    this.profile.update((p) => {
      if (!p) return p;
      const projects = [...p.projects];
      projects.splice(index + 1, 0, { ...projects[index] });
      return { ...p, projects };
    });
  }

  updateProject(index: number, field: 'name' | 'description', value: string): void {
    this.pushHistory();
    this.profile.update((p) => {
      if (!p) return p;
      const projects = [...p.projects];
      projects[index] = { ...projects[index], [field]: value };
      return { ...p, projects };
    });
  }

  addSkill(rawText: string): void {
    const value = rawText.trim();
    if (!value) return;
    this.pushHistory();
    this.profile.update((p) =>
      p ? { ...p, skills: [...p.skills, { raw_text: value, skill: null, evidence: null }] } : p,
    );
  }

  /** Assigns (or clears) a skill's category - stored on the same
   * `skill` ref the renderer already groups by, so a hand-typed group
   * name like "Backend & Frameworks" needs no new model field. Never
   * touches raw_text/evidence: this is presentation grouping, not a
   * re-classification of the underlying extracted fact. */
  updateSkillCategory(index: number, category: string): void {
    this.pushHistory();
    const trimmed = category.trim();
    this.profile.update((p) => {
      if (!p) return p;
      const skills = [...p.skills];
      const current = skills[index];
      skills[index] = {
        ...current,
        skill: trimmed
          ? { canonical_name: current.skill?.canonical_name ?? current.raw_text, category: trimmed }
          : null,
      };
      return { ...p, skills };
    });
  }

  addCertification(name: string): void {
    const value = name.trim();
    if (!value) return;
    this.pushHistory();
    this.profile.update((p) =>
      p
        ? { ...p, certifications: [...p.certifications, { name: value, issuer: null, date_raw: null, evidence: null }] }
        : p,
    );
  }

  addLanguage(name: string): void {
    const value = name.trim();
    if (!value) return;
    this.pushHistory();
    this.profile.update((p) =>
      p
        ? {
            ...p,
            languages: [
              ...p.languages,
              { name: value, proficiency: null, canonical_name: null, proficiency_normalized: null },
            ],
          }
        : p,
    );
  }

  removeListItem(list: 'skills' | 'certifications' | 'languages' | 'projects', index: number): void {
    this.pushHistory();
    this.profile.update((p) => {
      if (!p) return p;
      const updated = [...(p[list] as unknown[])];
      updated.splice(index, 1);
      return { ...p, [list]: updated } as CandidateProfile;
    });
  }

  undo(): void {
    const history = this.past();
    if (history.length === 0) return;
    const previous = history[history.length - 1];
    this.future.update((f) => [this.snapshot(), ...f]);
    this.past.set(history.slice(0, -1));
    this.restore(previous);
  }

  redo(): void {
    const upcoming = this.future();
    if (upcoming.length === 0) return;
    const next = upcoming[0];
    this.past.update((p) => [...p, this.snapshot()]);
    this.future.set(upcoming.slice(1));
    this.restore(next);
  }

  openExport(): void {
    const page = document.querySelector<HTMLElement>('.editor__preview .cv-page');
    // A4 height (297mm) at 96dpi - an estimate for the panel's copy, not
    // a guarantee; the real pagination happens server-side.
    const pageHeightPx = 1122;
    this.estimatedPages.set(page ? Math.max(1, Math.ceil(page.scrollHeight / pageHeightPx)) : 1);
    this.downloadError.set(null);
    this.showExport.set(true);
  }

  closeExport(): void {
    this.showExport.set(false);
  }

  /** Preview is a purely client-side visual of the current document -
   * it never calls the render-pdf endpoint, opens a browser tab, or
   * triggers any download/print flow. It is the same live-styled
   * renderer used in the main editing pane, just shown full-size in a
   * modal so the candidate can review it before committing to a
   * download. Triggered directly from the sections/undo/redo rail, so
   * it is independent of the export dialog - not nested inside it. */
  openPreview(): void {
    if (!this.profile()) return;
    this.showExport.set(false);
    this.showPreview.set(true);
  }

  closePreview(): void {
    this.showPreview.set(false);
  }

  downloadPdf(): void {
    const profile = this.profile();
    if (!profile || this.downloading()) return;

    this.downloading.set(true);
    this.downloadError.set(null);
    this.cvApi.renderPdf(this.renderPdfRequest(profile)).subscribe({
      next: (blob) => {
        this.downloading.set(false);
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        const name = (profile.full_name ?? 'cv').trim().replace(/\s+/g, '-').toLowerCase();
        link.download = `${name || 'cv'}.pdf`;
        document.body.appendChild(link);
        link.click();
        link.remove();
        URL.revokeObjectURL(url);
        this.showExport.set(false);
      },
      error: () => {
        this.downloading.set(false);
        this.downloadError.set('Could not generate the PDF. Please try again.');
      },
    });
  }

  private renderPdfRequest(profile: CandidateProfile): RenderPdfRequest {
    return {
      profile,
      template_id: this.templateId(),
      section_order: this.sectionOrder(),
      hidden_section_ids: this.hiddenSectionIds(),
      group_skills_by_category: this.groupSkillsByCategory(),
    };
  }

  private pushHistory(): void {
    this.past.update((p) => [...p, this.snapshot()]);
    this.future.set([]);
  }

  private snapshot(): EditorSnapshot {
    return structuredClone({
      profile: this.profile()!,
      sectionOrder: this.sectionOrder(),
      hiddenSectionIds: this.hiddenSectionIds(),
    });
  }

  private restore(snapshot: EditorSnapshot): void {
    this.profile.set(snapshot.profile);
    this.sectionOrder.set(snapshot.sectionOrder);
    this.hiddenSectionIds.set(snapshot.hiddenSectionIds);
  }
}
