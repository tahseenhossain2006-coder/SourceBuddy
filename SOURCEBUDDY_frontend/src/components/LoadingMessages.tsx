import { useEffect, useState } from 'react';
import { Spinner } from './Spinner';

/**
 * Contextual messages for long-running searches (~30-120s).
 *
 * These describe stages the pipeline actually performs (planning, search,
 * crawl, extraction, normalization, ranking). They do NOT claim AI analysis,
 * verification, or any backend operation the pipeline does not perform.
 */

const DEFAULT_MESSAGES = [
  'Preparing your sourcing request…',
  'Searching supplier sources…',
  'Collecting supplier pages…',
  'Extracting supplier details…',
  'Normalizing results…',
  'Preparing the shortlist…',
];

interface LoadingMessagesProps {
  messages?: string[];
  /** Advance interval in ms. Default 9000 (~total 45s before holding on the last). */
  intervalMs?: number;
  /** When true, the component stops advancing and shows a "still working" note. */
  stalled?: boolean;
}

export function LoadingMessages({
  messages = DEFAULT_MESSAGES,
  intervalMs = 9000,
  stalled = false,
}: LoadingMessagesProps) {
  const [index, setIndex] = useState(0);
  const lastIndex = messages.length - 1;

  useEffect(() => {
    if (stalled || index >= lastIndex) return;
    const t = window.setTimeout(() => setIndex((i) => Math.min(i + 1, lastIndex)), intervalMs);
    return () => window.clearTimeout(t);
  }, [index, intervalMs, lastIndex, stalled]);

  return (
    <div
      role="status"
      aria-live="polite"
      className="flex flex-col items-center gap-4 py-10 text-center"
    >
      <Spinner size="lg" />
      <p className="font-mono text-[11px] uppercase tracking-[.28em] text-acc/90">
        {messages[index]}
      </p>
      <p className="max-w-sm text-xs text-white/40 leading-relaxed">
        This can take up to two minutes. Please don&rsquo;t close the tab.
      </p>
    </div>
  );
}