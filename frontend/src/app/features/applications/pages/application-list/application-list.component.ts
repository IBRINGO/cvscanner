import { ChangeDetectionStrategy, Component } from '@angular/core';
import { PlaceholderPageComponent } from '../../../../shared/components/ui/placeholder-page/placeholder-page.component';

@Component({
  selector: 'app-application-list-page',
  standalone: true,
  imports: [PlaceholderPageComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <app-placeholder-page
      title="Applications"
      description="Track applications you've submitted and their status. Not scheduled in the current 5-phase plan."
    />
  `,
})
export class ApplicationListComponent {}
