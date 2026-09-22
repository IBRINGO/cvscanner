import { ChangeDetectionStrategy, Component } from '@angular/core';
import { PlaceholderPageComponent } from '../../../../shared/components/ui/placeholder-page/placeholder-page.component';

@Component({
  selector: 'app-settings-page',
  standalone: true,
  imports: [PlaceholderPageComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <app-placeholder-page
      title="Settings"
      description="Account and application preferences. Will grow alongside authentication."
    />
  `,
})
export class SettingsPageComponent {}
