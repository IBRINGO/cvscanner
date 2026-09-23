import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { SidebarComponent } from './sidebar.component';
import { SidebarStateService } from './sidebar-state.service';

describe('SidebarComponent', () => {
  let fixture: ComponentFixture<SidebarComponent>;
  let state: SidebarStateService;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [SidebarComponent],
      providers: [provideRouter([])],
    });
    fixture = TestBed.createComponent(SidebarComponent);
    state = TestBed.inject(SidebarStateService);
    fixture.detectChanges();
  });

  it('reflects the collapsed state on the nav element', () => {
    const nav = (fixture.nativeElement as HTMLElement).querySelector('.app-sidebar')!;
    expect(nav.getAttribute('data-collapsed')).toBe('false');

    state.toggleCollapsed();
    fixture.detectChanges();
    expect(nav.getAttribute('data-collapsed')).toBe('true');
  });

  it('shows a backdrop only when the mobile drawer is open', () => {
    expect((fixture.nativeElement as HTMLElement).querySelector('.app-sidebar__backdrop')).toBeNull();

    state.openMobile();
    fixture.detectChanges();
    expect((fixture.nativeElement as HTMLElement).querySelector('.app-sidebar__backdrop')).not.toBeNull();
  });

  it('closes the mobile drawer when a nav link is clicked', () => {
    state.openMobile();
    fixture.detectChanges();
    (fixture.nativeElement as HTMLElement).querySelector<HTMLAnchorElement>('.app-sidebar__link')!.click();
    expect(state.mobileOpen()).toBeFalse();
  });

  it('renders every nav item label', () => {
    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    for (const label of ['Workspace', 'Applications', 'CV Library', 'Templates', 'Settings']) {
      expect(text).toContain(label);
    }
  });
});
