import { ChangeDetectionStrategy, Component } from '@angular/core';
import { PlaceholderPageComponent } from '../../../../shared/components/ui/placeholder-page/placeholder-page.component';

@Component({
  selector: 'app-analysis-list-page',
  standalone: true,
  imports: [PlaceholderPageComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <app-placeholder-page
      title="Analysis"
      description="Explainable ATS match scores, skill/requirement breakdowns, and evidence. The ATS Intelligence Engine lands in Phases 3-4."
    />
  `,
})
export class AnalysisListComponent {}
