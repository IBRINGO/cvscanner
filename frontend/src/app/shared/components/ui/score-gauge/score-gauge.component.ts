import { ChangeDetectionStrategy, Component, ElementRef, Input, OnChanges, inject, signal } from '@angular/core';

/**
 * The primary ATS score visualization: an animated semicircular gauge,
 * modelled on a measurement instrument (a speedometer), because the
 * product's core claim is "we measured this", not "we generated this".
 * The rendered number is always exactly the score passed in - the
 * animation communicates progress toward a real value, it never implies
 * a value beyond what the backend returned.
 */
@Component({
  selector: 'app-score-gauge',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="gauge" [attr.data-size]="size">
      <svg [attr.viewBox]="'0 0 220 132'" class="gauge__svg" role="img" [attr.aria-label]="ariaLabel()">
        <path [attr.d]="arcPath" class="gauge__track" />
        <path
          [attr.d]="arcPath"
          class="gauge__fill"
          [attr.stroke]="fillColor()"
          [style.strokeDasharray]="arcLength"
          [style.strokeDashoffset]="dashOffset()"
        />
      </svg>
      <div class="gauge__readout">
        <span class="gauge__number font-display" [style.color]="fillColor()">{{ displayValue() }}</span>
        @if (label) {
          <span class="gauge__label">{{ label }}</span>
        }
      </div>
      <div class="gauge__scale" aria-hidden="true">
        <span>Low</span>
        <span>Medium</span>
        <span>High</span>
      </div>
    </div>
  `,
  styles: [
    `
      .gauge {
        display: inline-flex;
        flex-direction: column;
        align-items: center;
        width: 100%;
        max-width: 320px;
      }
      .gauge__svg {
        width: 100%;
        height: auto;
        overflow: visible;
      }
      .gauge__track {
        fill: none;
        stroke: var(--surface-sunken);
        stroke-width: 16;
        stroke-linecap: round;
      }
      .gauge__fill {
        fill: none;
        stroke-width: 16;
        stroke-linecap: round;
        transition: stroke-dashoffset var(--motion-reveal) var(--motion-ease);
      }
      .gauge__readout {
        display: flex;
        flex-direction: column;
        align-items: center;
        margin-top: calc(var(--space-7) * -1);
        gap: var(--space-1);
      }
      .gauge__number {
        font-size: var(--text-4xl);
        font-weight: 600;
        line-height: 1;
        font-variant-numeric: tabular-nums;
      }
      .gauge__label {
        font-size: var(--text-xs);
        font-weight: 600;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: var(--ink-tertiary);
      }
      .gauge__scale {
        display: flex;
        justify-content: space-between;
        width: 82%;
        margin-top: var(--space-2);
        font-size: var(--text-xs);
        color: var(--ink-tertiary);
      }
      [data-size='md'] {
        max-width: 220px;
      }
      [data-size='md'] .gauge__number {
        font-size: var(--text-2xl);
      }
      [data-size='md'] .gauge__readout {
        margin-top: calc(var(--space-6) * -1);
      }
      @media (prefers-reduced-motion: reduce) {
        .gauge__fill {
          transition: none;
        }
      }
    `,
  ],
})
export class ScoreGaugeComponent implements OnChanges {
  @Input({ required: true }) score!: number;
  @Input() label = 'ATS Match';
  @Input() size: 'lg' | 'md' = 'lg';

  private readonly host = inject(ElementRef<HTMLElement>);
  private readonly animated = signal(0);
  private frame: number | null = null;

  protected readonly arcLength = 90 * Math.PI;
  protected readonly arcPath = 'M 20 116 A 90 90 0 0 1 200 116';

  ngOnChanges(): void {
    const target = this.clamp(this.score);
    if (this.prefersReducedMotion()) {
      this.animated.set(target);
      return;
    }
    this.animateTo(target);
  }

  dashOffset(): number {
    return this.arcLength * (1 - this.animated());
  }

  displayValue(): number {
    return Math.round(this.animated() * 100);
  }

  ariaLabel(): string {
    return `${this.label}: ${Math.round(this.clamp(this.score) * 100)} out of 100`;
  }

  fillColor(): string {
    const pct = this.animated();
    if (pct >= 0.8) return 'var(--positive)';
    if (pct >= 0.6) return 'var(--accent)';
    if (pct >= 0.35) return 'var(--attention)';
    return 'var(--negative)';
  }

  private animateTo(target: number): void {
    if (this.frame !== null) {
      cancelAnimationFrame(this.frame);
    }
    const start = this.animated();
    const duration = 900;
    const startTime = performance.now();
    const step = (now: number) => {
      const elapsed = now - startTime;
      const t = Math.min(1, elapsed / duration);
      const eased = 1 - Math.pow(1 - t, 3);
      this.animated.set(start + (target - start) * eased);
      if (t < 1) {
        this.frame = requestAnimationFrame(step);
      } else {
        this.frame = null;
      }
    };
    this.frame = requestAnimationFrame(step);
  }

  private prefersReducedMotion(): boolean {
    return this.host.nativeElement.ownerDocument.defaultView?.matchMedia?.(
      '(prefers-reduced-motion: reduce)',
    ).matches ?? false;
  }

  private clamp(value: number): number {
    return Math.min(1, Math.max(0, value ?? 0));
  }
}
