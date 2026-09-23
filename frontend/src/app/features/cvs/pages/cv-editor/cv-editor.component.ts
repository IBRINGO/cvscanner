import { ChangeDetectionStrategy, Component, OnInit, computed, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { NgIcon, provideIcons } from '@ng-icons/core';
import { CVSCANNER_ICONS } from '../../../../core/icons';
import { CvDocumentRendererComponent } from '../../../templates/components/cv-document-renderer/cv-document-renderer.component';
import { CV_TEMPLATES, TemplateDefinition, findTemplate } from '../../../templates/models/template-definition.model';
import { CandidateProfile, Experience } from '../../models/candidate-profile.model';
import {
  CustomSectionRef,
  CvSectionRef,
  DEFAULT_SECTION_ORDER,
  SECTION_LABELS,
} from '../../models/cv-document.model';
import { EditorSnapshot } from '../../models/editor-state.model';
import { CvApiService } from '../../services/cv-api.service';

/**
 * The CV editor: structured editing over the same CandidateProfile the
 * rest of the product already trusts, rendered live through the same
 * CvDocumentRenderer templates will use for export. Deliberately
 * client-side only - edits here never call a backend endpoint that
 * would let free-text bypass the Truth Layer's claim validation
 * (see docs/architecture/phase-6-frontend-redesign.md). Reordering,
 * hiding, and rewording existing text is always safe because it is the
 * candidate's own hand-typed edit, not an AI-generated claim.
 */
@Component({
  selector: 'app-cv-editor-page',
  standalone: true,
  imports: [RouterLink, FormsModule, NgIcon, CvDocumentRendererComponent],
  viewProviders: [provideIcons(CVSCANNER_ICONS)],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="editor__topbar">
      <a [routerLink]="['/cvs', documentId]" class="editor__back text-secondary">Back to CV</a>
      @if (profile()) {
        <button type="button" class="editor__export-trigger" (click)="openExport()">
          <ng-icon name="lucideFileCheck" size="15" />
          Export
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
              <dt>ATS-friendly</dt>
              <dd><ng-icon name="lucideCircleCheck" size="14" /> Plain text, no images</dd>
            </div>
          </dl>
          <div class="editor__export-actions">
            <button type="button" class="editor__export-download" (click)="downloadPdf()">
              <ng-icon name="lucideFileUp" size="15" />
              Download PDF
            </button>
            <button type="button" class="editor__export-cancel" (click)="closeExport()">Continue editing</button>
          </div>
          <p class="text-tertiary editor__export-note">
            DOCX export is not available yet. PDF preserves your selected template exactly.
          </p>
        </div>
      </div>
    }

    @if (loading()) {
      <p class="text-secondary">Loading your CV...</p>
    } @else if (!profile()) {
      <p class="text-secondary">This CV has no extracted profile yet.</p>
    } @else {
      <div class="editor">
        <aside class="editor__panel editor__sections">
          <div class="editor__field">
            <label class="editor__label" for="template-select">Template</label>
            <select id="template-select" class="editor__select" [ngModel]="templateId()" (ngModelChange)="templateId.set($event)">
              @for (t of templates; track t.id) {
                <option [value]="t.id">{{ t.name }}</option>
              }
            </select>
            <a routerLink="/templates" class="editor__gallery-link">Browse all templates</a>
          </div>

          <div class="editor__field">
            <span class="editor__label">Sections</span>
            <ul class="editor__section-list">
              @for (ref of sectionOrder(); track ref.id; let i = $index) {
                <li
                  class="editor__section-row"
                  [attr.data-selected]="selectedSectionId() === ref.id"
                  [attr.data-hidden]="hiddenSectionIds().includes(ref.id)"
                >
                  <button type="button" class="editor__section-name" (click)="selectedSectionId.set(ref.id)">
                    {{ labelFor(ref) }}
                  </button>
                  <div class="editor__section-actions">
                    <button type="button" title="Move up" [disabled]="i === 0" (click)="moveSection(i, -1)">
                      <ng-icon name="lucideChevronRight" size="13" class="editor__icon-up" />
                    </button>
                    <button
                      type="button"
                      title="Move down"
                      [disabled]="i === sectionOrder().length - 1"
                      (click)="moveSection(i, 1)"
                    >
                      <ng-icon name="lucideChevronRight" size="13" class="editor__icon-down" />
                    </button>
                    <button
                      type="button"
                      [title]="hiddenSectionIds().includes(ref.id) ? 'Show section' : 'Hide section'"
                      (click)="toggleHidden(ref.id)"
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

          <div class="editor__history">
            <button type="button" [disabled]="!canUndo()" (click)="undo()">Undo</button>
            <button type="button" [disabled]="!canRedo()" (click)="redo()">Redo</button>
          </div>
        </aside>

        <div class="editor__preview">
          <app-cv-document-renderer
            [profile]="profile()!"
            [sectionOrder]="sectionOrder()"
            [hiddenSectionIds]="hiddenSectionIds()"
            [template]="currentTemplate()"
          />
        </div>

        <aside class="editor__panel editor__properties">
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
              @for (exp of profile()!.experiences; track $index; let i = $index) {
                <div class="editor__entry-card">
                  <label class="editor__field">
                    <span class="editor__label">Role</span>
                    <input type="text" [ngModel]="exp.title ?? ''" (ngModelChange)="updateExperience(i, 'title', $event)" />
                  </label>
                  <label class="editor__field">
                    <span class="editor__label">Company</span>
                    <input type="text" [ngModel]="exp.company ?? ''" (ngModelChange)="updateExperience(i, 'company', $event)" />
                  </label>
                  <label class="editor__field">
                    <span class="editor__label">Description</span>
                    <textarea rows="3" [ngModel]="exp.description ?? ''" (ngModelChange)="updateExperience(i, 'description', $event)"></textarea>
                  </label>
                </div>
              }
            }
            @case ('education') {
              @for (entry of profile()!.education; track $index; let i = $index) {
                <div class="editor__entry-card">
                  <label class="editor__field">
                    <span class="editor__label">Degree</span>
                    <input type="text" [ngModel]="entry.degree ?? ''" (ngModelChange)="updateEducation(i, 'degree', $event)" />
                  </label>
                  <label class="editor__field">
                    <span class="editor__label">Institution</span>
                    <input type="text" [ngModel]="entry.institution ?? ''" (ngModelChange)="updateEducation(i, 'institution', $event)" />
                  </label>
                </div>
              }
            }
            @case ('skills') {
              <ul class="editor__chip-list">
                @for (skill of profile()!.skills; track $index; let i = $index) {
                  <li>
                    {{ skill.skill?.canonical_name ?? skill.raw_text }}
                    <button type="button" title="Remove from CV" (click)="removeListItem('skills', i)">
                      <ng-icon name="lucideX" size="12" />
                    </button>
                  </li>
                }
              </ul>
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
            }
            @case ('projects') {
              <ul class="editor__chip-list">
                @for (project of profile()!.projects; track $index; let i = $index) {
                  <li>
                    {{ project.name }}
                    <button type="button" title="Remove from CV" (click)="removeListItem('projects', i)">
                      <ng-icon name="lucideX" size="12" />
                    </button>
                  </li>
                }
              </ul>
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
        </aside>
      </div>
    }
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

  private readonly past = signal<EditorSnapshot[]>([]);
  private readonly future = signal<EditorSnapshot[]>([]);
  readonly canUndo = computed(() => this.past().length > 0);
  readonly canRedo = computed(() => this.future().length > 0);

  readonly showExport = signal(false);
  readonly estimatedPages = signal(1);

  protected readonly currentTemplate = computed<TemplateDefinition>(() => findTemplate(this.templateId()));
  protected readonly selectedRef = computed<CvSectionRef | undefined>(() =>
    this.sectionOrder().find((ref) => ref.id === this.selectedSectionId()),
  );

  private readonly route = inject(ActivatedRoute);

  constructor(private readonly cvApi: CvApiService) {
    this.documentId = this.route.snapshot.paramMap.get('id') ?? '';
  }

  ngOnInit(): void {
    const requestedTemplate = this.route.snapshot.queryParamMap.get('template');
    if (requestedTemplate && this.templates.some((t) => t.id === requestedTemplate)) {
      this.templateId.set(requestedTemplate);
    }

    if (!this.documentId) {
      this.loading.set(false);
      return;
    }
    this.cvApi.getProfile(this.documentId).subscribe({
      next: (response) => {
        this.profile.set(response.profile);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
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

  moveSection(index: number, direction: -1 | 1): void {
    const target = index + direction;
    const order = this.sectionOrder();
    if (target < 0 || target >= order.length) return;
    this.pushHistory();
    const next = [...order];
    [next[index], next[target]] = [next[target], next[index]];
    this.sectionOrder.set(next);
  }

  toggleHidden(id: string): void {
    this.pushHistory();
    this.hiddenSectionIds.update((ids) => (ids.includes(id) ? ids.filter((i) => i !== id) : [...ids, id]));
  }

  addCustomSection(): void {
    this.pushHistory();
    const id = `custom-${Date.now()}`;
    const section: CustomSectionRef = { id, kind: 'custom', title: 'New section', content: '' };
    this.sectionOrder.update((order) => [...order, section]);
    this.selectedSectionId.set(id);
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

  updateSummary(value: string): void {
    this.pushHistory();
    this.profile.update((p) => (p ? { ...p, summary: value } : p));
  }

  updateExperience(index: number, field: keyof Pick<Experience, 'title' | 'company' | 'description'>, value: string): void {
    this.pushHistory();
    this.profile.update((p) => {
      if (!p) return p;
      const experiences = [...p.experiences];
      experiences[index] = { ...experiences[index], [field]: value };
      return { ...p, experiences };
    });
  }

  updateEducation(index: number, field: 'degree' | 'institution', value: string): void {
    this.pushHistory();
    this.profile.update((p) => {
      if (!p) return p;
      const education = [...p.education];
      education[index] = { ...education[index], [field]: value };
      return { ...p, education };
    });
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
    const page = document.querySelector<HTMLElement>('.cv-page');
    // ~1000px of rendered content per printed page at 96dpi, after
    // typical margins - an estimate, not a guarantee, and labelled as
    // such in the panel.
    const pageHeightPx = 1000;
    this.estimatedPages.set(page ? Math.max(1, Math.ceil(page.scrollHeight / pageHeightPx)) : 1);
    this.showExport.set(true);
  }

  closeExport(): void {
    this.showExport.set(false);
  }

  downloadPdf(): void {
    document.body.classList.add('cv-printing');
    const cleanup = () => {
      document.body.classList.remove('cv-printing');
      window.removeEventListener('afterprint', cleanup);
    };
    window.addEventListener('afterprint', cleanup);
    window.print();
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
