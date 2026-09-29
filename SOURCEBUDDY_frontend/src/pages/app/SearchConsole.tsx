import { useEffect, useRef, useState } from 'react';
import type { FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { AppShell } from '@/layouts/AppShell';
import { Button } from '@/components/Button';
import { ErrorBanner } from '@/components/ErrorBanner';
import { LoadingMessages } from '@/components/LoadingMessages';
import { runSearch } from '@/api/search';
import { rememberSearch } from './useSearch';

export default function SearchConsole() {
  const navigate = useNavigate();
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const [stalled, setStalled] = useState(false);
  const inFlight = useRef(false);

  useEffect(() => {
    if (!loading) {
      setStalled(false);
      return;
    }
    const t = window.setTimeout(() => setStalled(true), 90_000);
    return () => window.clearTimeout(t);
  }, [loading]);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const trimmed = query.trim();
    if (!trimmed) return;
    if (inFlight.current) return;

    inFlight.current = true;
    setError(null);
    setLoading(true);
    try {
      const res = await runSearch({ query: trimmed });
      const data = res.data;
      rememberSearch(data);
      navigate(`/app/search/${encodeURIComponent(data.search_id)}`);
    } catch (err) {
      setError(err);
    } finally {
      inFlight.current = false;
      setLoading(false);
    }
  }

  return (
    <AppShell>
      <div className="max-w-3xl mx-auto">
        <p className="font-mono text-[11px] tracking-[.28em] uppercase text-acc/90">
          New search
        </p>
        <h1 className="mt-4 font-display italic text-4xl sm:text-5xl text-white">
          Describe what you need.
        </h1>
        <p className="mt-3 max-w-xl text-sm text-white/55 leading-relaxed">
          One sentence. Product, quantity, and destination if you know them.
        </p>

        {loading ? (
          <div className="mt-10">
            <LoadingMessages stalled={stalled} />
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="mt-10 flex flex-col gap-4">
            <label
              htmlFor="search-query"
              className="font-mono text-[11px] uppercase tracking-[.18em] text-white/50"
            >
              Sourcing query
            </label>
            <textarea
              id="search-query"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              disabled={loading}
              rows={3}
              placeholder="e.g. stainless steel bottle supplier India MOQ 500"
              className="w-full resize-y rounded-2xl border border-white/15 bg-white/[.05] px-5 py-4 text-sm leading-relaxed text-white placeholder:text-white/25 focus:outline-none focus:border-acc/60 focus:bg-white/[.08] transition-colors"
            />
            {error ? <ErrorBanner error={error} onRetry={() => { /* user can resubmit */ }} /> : null}
            <div className="flex items-center gap-4">
              <Button type="submit" loading={loading} disabled={!query.trim()}>
                Run search
              </Button>
              <p className="font-mono text-[10px] tracking-[.22em] text-white/35">
                Takes 30–120 SECONDS
              </p>
            </div>
          </form>
        )}
      </div>
    </AppShell>
  );
}