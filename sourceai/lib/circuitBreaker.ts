// lib/circuitBreaker.ts
interface CircuitState {
  failures: number;
  lastFailure: number;
  state: 'CLOSED' | 'OPEN' | 'HALF_OPEN';
}

export class CircuitBreaker {
  private static instances = new Map<string, CircuitState>();
  private static readonly FAILURE_THRESHOLD = 3;
  private static readonly OPEN_TIMEOUT_MS = 60000; // 1 minute

  static recordSuccess(provider: string) {
    const state = this.instances.get(provider);
    if (state) {
      state.failures = 0;
      state.state = 'CLOSED';
    }
  }

  static recordFailure(provider: string) {
    const state = this.instances.get(provider) || { failures: 0, lastFailure: 0, state: 'CLOSED' };
    state.failures += 1;
    state.lastFailure = Date.now();
    if (state.failures >= this.FAILURE_THRESHOLD) {
      state.state = 'OPEN';
    }
    this.instances.set(provider, state);
  }

  static isAvailable(provider: string): boolean {
    const state = this.instances.get(provider);
    if (!state) return true;
    if (state.state === 'OPEN') {
      const elapsed = Date.now() - state.lastFailure;
      if (elapsed > this.OPEN_TIMEOUT_MS) {
        state.state = 'HALF_OPEN';
        return true;
      }
      return false;
    }
    return true;
  }
}