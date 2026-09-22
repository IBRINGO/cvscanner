import { ChangeDetectionStrategy, Component } from '@angular/core';
import { PlaceholderPageComponent } from '../../../../shared/components/ui/placeholder-page/placeholder-page.component';

@Component({
  selector: 'app-tailoring-config-page',
  standalone: true,
  imports: [PlaceholderPageComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <app-placeholder-page
      title="Tailoring"
      description="Generate an adapted CV and validate it against the evidence in your original CV. Lands in Phase 5."
    />
  `,
})
export class TailoringConfigComponent {}
