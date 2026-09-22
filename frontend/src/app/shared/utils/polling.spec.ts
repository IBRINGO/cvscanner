import { of } from 'rxjs';
import { pollUntilDone } from './polling';

describe('pollUntilDone', () => {
  it('stops once isDone returns true, including the done value', (done) => {
    const values = [{ status: 'PROCESSING' }, { status: 'PROCESSED' }];
    let callIndex = 0;
    const source = () => of(values[Math.min(callIndex++, values.length - 1)]);

    const results: { status: string }[] = [];
    pollUntilDone(source, (value) => value.status === 'PROCESSED', 0).subscribe({
      next: (value) => results.push(value),
      complete: () => {
        expect(results.map((r) => r.status)).toEqual(['PROCESSING', 'PROCESSED']);
        done();
      },
    });
  });

  it('emits immediately without waiting for the first interval tick', (done) => {
    pollUntilDone(() => of({ status: 'PROCESSED' }), () => true, 5000).subscribe({
      next: (value) => {
        expect(value.status).toBe('PROCESSED');
        done();
      },
    });
  });
});
