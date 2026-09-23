import { TestBed } from '@angular/core/testing';
import { SidebarStateService } from './sidebar-state.service';

describe('SidebarStateService', () => {
  let service: SidebarStateService;

  beforeEach(() => {
    try {
      localStorage.removeItem('cvscanner.sidebar.collapsed');
    } catch {
      /* ignore */
    }
    TestBed.configureTestingModule({});
    service = TestBed.inject(SidebarStateService);
  });

  it('starts expanded by default', () => {
    expect(service.collapsed()).toBeFalse();
  });

  it('toggles and persists the collapsed state', () => {
    service.toggleCollapsed();
    expect(service.collapsed()).toBeTrue();
    expect(localStorage.getItem('cvscanner.sidebar.collapsed')).toBe('true');

    service.toggleCollapsed();
    expect(service.collapsed()).toBeFalse();
  });

  it('opens and closes the mobile drawer independently of the collapsed state', () => {
    expect(service.mobileOpen()).toBeFalse();
    service.openMobile();
    expect(service.mobileOpen()).toBeTrue();
    service.closeMobile();
    expect(service.mobileOpen()).toBeFalse();
  });
});
