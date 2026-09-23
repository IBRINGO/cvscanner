import { ComponentFixture, TestBed } from '@angular/core/testing';
import { DocumentPreviewComponent } from './document-preview.component';

describe('DocumentPreviewComponent', () => {
  let fixture: ComponentFixture<DocumentPreviewComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({ imports: [DocumentPreviewComponent] });
    fixture = TestBed.createComponent(DocumentPreviewComponent);
  });

  it('shows the real heading text passed in, not a placeholder, once provided', () => {
    fixture.componentInstance.kind = 'cv';
    fixture.componentInstance.heading = 'Boureima Ibringo';
    fixture.detectChanges();
    expect((fixture.nativeElement as HTMLElement).textContent).toContain('Boureima Ibringo');
  });

  it('falls back to an honest processing message when no heading is available yet', () => {
    fixture.componentInstance.kind = 'job';
    fixture.detectChanges();
    expect((fixture.nativeElement as HTMLElement).textContent).toContain('Processing document...');
  });

  it('shows a status badge only when a status is provided', () => {
    fixture.componentInstance.kind = 'cv';
    fixture.componentInstance.status = 'PROCESSED';
    fixture.detectChanges();
    expect((fixture.nativeElement as HTMLElement).querySelector('app-status-badge')).toBeTruthy();
  });
});
