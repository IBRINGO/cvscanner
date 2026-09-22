import { ChangeDetectionStrategy, Component } from '@angular/core';
import { PlaceholderPageComponent } from '../../../../shared/components/ui/placeholder-page/placeholder-page.component';

@Component({
  selector: 'app-recommendations-page',
  standalone: true,
  imports: [PlaceholderPageComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <app-placeholder-page
      title="Recommendations"
      description="Actionable, prioritized suggestions to close gaps against a job. Lands in Phase 4."
    />
  `,
})
export class RecommendationsPageComponent {}
