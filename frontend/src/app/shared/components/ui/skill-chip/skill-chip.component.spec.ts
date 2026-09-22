import { ComponentFixture, TestBed } from '@angular/core/testing';
import { SkillChipComponent } from './skill-chip.component';

describe('SkillChipComponent', () => {
  let fixture: ComponentFixture<SkillChipComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({ imports: [SkillChipComponent] });
    fixture = TestBed.createComponent(SkillChipComponent);
  });

  it('shows the canonical name when the skill matched the taxonomy', () => {
    fixture.componentInstance.rawText = 'js';
    fixture.componentInstance.skill = { canonical_name: 'JavaScript', category: 'PROGRAMMING_LANGUAGE' };
    fixture.detectChanges();

    const button = (fixture.nativeElement as HTMLElement).querySelector('.skill-chip');
    expect(button?.getAttribute('data-matched')).toBe('true');
    expect(button?.textContent).toContain('JavaScript');
  });

  it('marks an unmatched skill as unmatched and shows the raw text', () => {
    fixture.componentInstance.rawText = 'SomeInternalTool';
    fixture.componentInstance.skill = null;
    fixture.detectChanges();

    const button = (fixture.nativeElement as HTMLElement).querySelector('.skill-chip');
    expect(button?.getAttribute('data-matched')).toBe('false');
    expect(button?.textContent).toContain('SomeInternalTool');
  });

  it('reveals evidence only after being clicked', () => {
    fixture.componentInstance.rawText = 'Python';
    fixture.componentInstance.skill = { canonical_name: 'Python', category: 'PROGRAMMING_LANGUAGE' };
    fixture.componentInstance.evidence = {
      page_number: 2,
      section: 'SKILLS',
      text: 'Python, Django',
      confidence: 0.95,
      extraction_method: 'RULE',
    };
    fixture.detectChanges();

    expect((fixture.nativeElement as HTMLElement).querySelector('app-evidence-note')).toBeNull();

    (fixture.nativeElement as HTMLElement).querySelector<HTMLButtonElement>('.skill-chip')!.click();
    fixture.detectChanges();

    expect((fixture.nativeElement as HTMLElement).querySelector('app-evidence-note')).not.toBeNull();
  });
});
