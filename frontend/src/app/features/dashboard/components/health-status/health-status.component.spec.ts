import { ComponentFixture, TestBed } from '@angular/core/testing';
import { of, throwError } from 'rxjs';
import { HealthService } from '../../services/health.service';
import { HealthResponse } from '../../models/health.model';
import { HealthStatusComponent } from './health-status.component';

describe('HealthStatusComponent', () => {
  let fixture: ComponentFixture<HealthStatusComponent>;
  let healthServiceSpy: jasmine.SpyObj<HealthService>;

  function setup(): void {
    fixture = TestBed.createComponent(HealthStatusComponent);
    fixture.detectChanges();
  }

  it('shows the backend status when the health check succeeds', () => {
    const response: HealthResponse = { status: 'ok', service: 'cvscanner-backend', version: '0.1.0' };
    healthServiceSpy = jasmine.createSpyObj('HealthService', ['check']);
    healthServiceSpy.check.and.returnValue(of(response));

    TestBed.configureTestingModule({
      imports: [HealthStatusComponent],
      providers: [{ provide: HealthService, useValue: healthServiceSpy }],
    });

    setup();

    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(text).toContain('Backend available');
    expect(text).toContain('cvscanner-backend');
  });

  it('shows an unavailable message when the health check fails', () => {
    healthServiceSpy = jasmine.createSpyObj('HealthService', ['check']);
    healthServiceSpy.check.and.returnValue(throwError(() => new Error('network error')));

    TestBed.configureTestingModule({
      imports: [HealthStatusComponent],
      providers: [{ provide: HealthService, useValue: healthServiceSpy }],
    });

    setup();

    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(text).toContain('Backend unavailable');
  });
});
