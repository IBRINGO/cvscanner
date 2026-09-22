import { Observable, timer } from 'rxjs';
import { switchMap, takeWhile } from 'rxjs/operators';

/**
 * Polls `source()` every `intervalMs` until `isDone(value)` returns true
 * (inclusive - the done value is still emitted). Stops automatically on
 * unsubscribe (component destroy via `takeUntilDestroyed`, see callers),
 * so there is never more than one polling subscription per caller and no
 * leaked interval once the component is gone (section 53).
 */
export function pollUntilDone<T>(
  source: () => Observable<T>,
  isDone: (value: T) => boolean,
  intervalMs = 2000,
): Observable<T> {
  return timer(0, intervalMs).pipe(
    switchMap(() => source()),
    takeWhile((value) => !isDone(value), true),
  );
}
