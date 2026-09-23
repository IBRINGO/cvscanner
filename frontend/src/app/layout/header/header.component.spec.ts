import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { HeaderComponent } from './header.component';
import { SidebarStateService } from '../sidebar/sidebar-state.service';

describe('HeaderComponent', () => {
  let fixture: ComponentFixture<HeaderComponent>;
  let state: SidebarStateService;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HeaderComponent],
      providers: [provideRouter([])],
    });
    fixture = TestBed.createComponent(HeaderComponent);
    state = TestBed.inject(SidebarStateService);
    fixture.detectChanges();
  });

  it('opens the mobile sidebar drawer when the menu trigger is clicked', () => {
    expect(state.mobileOpen()).toBeFalse();
    (fixture.nativeElement as HTMLElement).querySelector<HTMLButtonElement>('.app-header__menu-trigger')!.click();
    expect(state.mobileOpen()).toBeTrue();
  });

  it('shows the CVScanner brand mark', () => {
    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(text).toContain('CVScanner');
  });
});
