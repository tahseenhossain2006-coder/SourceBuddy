// lib/concurrency.ts
export async function runWithConcurrency<T, R>(
  items: T[],
  concurrency: number,
  fn: (item: T) => Promise<R>
): Promise<R[]> {
  const results: R[] = [];
  const queue = [...items];
  const inProgress = new Set<Promise<void>>();

  const processNext = async () => {
    if (queue.length === 0) return;
    const item = queue.shift()!;
    const promise = fn(item).then((result) => {
      results.push(result);
      inProgress.delete(promise);
    });
    inProgress.add(promise);
    await promise;
    // Continue with next
    await processNext();
  };

  const workers = Array.from({ length: Math.min(concurrency, items.length) }, () => processNext());
  await Promise.all(workers);
  return results;
}