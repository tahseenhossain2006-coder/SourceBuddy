import { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { AppShell } from '@/layouts/AppShell';
import { Button } from '@/components/Button';
import { EmptyState } from '@/components/EmptyState';
import { ErrorBanner } from '@/components/ErrorBanner';
import { LoadingMessages } from '@/components/LoadingMessages';
import { SupplierCard } from '@/components/SupplierCard';
import { getSearch } from '@/api/search';
import { ApiError } from '@/lib/errors';
import { recallSearch } from './useSearch';
import type { SearchDetailData } from '@/types';

export default function SearchDetail() {
  const { searchId } = useParams<{ searchId: string }>();
  const navigate = useNavigate();

  const remembered = searchId ? recallSearch(searchId) : undefined;
  const [query, setQuery] = useState<string | null>(remembered?.query ?? null);

  const [data, setData] = useState<SearchDetailData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<unknown>(null);
  const [notPersisted, setNotPersisted] = useState(false);

  const [selected, setSelected] = useState<Set<number>>(new Set());

  useEffect(() => {
    if (!searchId) return;
    let cancelled = false;
    setLoading(true);
    setError(null);
    setNotPersisted(false);
    setSelected(new Set());

    (async () => {
      try {
        const res = await getSearch(searchId);
        if (cancelled) return;
        setData(res.data);
        setQuery(res.data.query);
      } catch (err) {
        if (cancelled) return;
        if (err instanceof ApiError && err.status === 404) {
          setNotPersisted(true);
        } else {
          setError(err);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [searchId]);

  function toggleSelect(index: number) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(index)) next.delete(index);
      else next.add(index);
      return next;
    });
  }

  function goToCompare() {
    if (!data || !searchId) return;
    const chosen = Array.from(selected)
      .sort((a, b) => a - b)
      .map((i) => data.suppliers[i])
      .filter(Boolean);
    if (chosen.length < 2) return;
    navigate('/app/compare', {
      state: { suppliers: chosen, query: data.query },
    });
  }

  return (
    <AppShell>
      <div className="max-w-4xl mx-auto pb-32">
        <button
          type="button"
          onClick={() => navigate('/app/search')}
          className="font-mono text-[10px] tracking-[.22em] uppercase text-white/40 hover:text-white/70 transition-colors"
        >
          ← New search
        </button>

        {query ? (
          <>
            <p className="mt-6 font-mono text-[11px] tracking-[.28em] uppercase text-acc/90">
              Search detail
            </p>
            <h1 className="mt-3 font-display italic text-3xl sm:text-4xl text-white break-words">
              {query}
            </h1>
          </>
        ) : null}

        {loading ? (
          <div className="mt-10">
            <LoadingMessages stalled={false} />
          </div>
        ) : null}

        {error ? (
          <div className="mt-10">
            <ErrorBanner error={error} onRetry={() => { setError(null); setLoading(true); }} />
          </div>
        ) : null}

        {notPersisted ? (
          <div className="mt-10">
            <EmptyState
              title="This search is not retrievable."
              description="The search ran, but the backend did not persist the result. You can run it again to see fresh results."
              action={
                <Link to="/app/search">
                  <Button variant="secondary">Run a new search</Button>
                </Link>
              }
            />
          </div>
        ) : null}

        {!loading && !error && !notPersisted && data ? (
          <>
            <div className="mt-8 flex items-center gap-4">
              <p className="font-mono text-[10px] tracking-[.22em] text-white/40">
                {data.suppliers.length}{' '}
                {data.suppliers.length === 1 ? 'SUPPLIER' : 'SUPPLIERS'}
              </p>
              <p className="font-mono text-[10px] tracking-[.22em] text-white/30">
                {data.status.toUpperCase()}
              </p>
            </div>

            {data.suppliers.length === 0 ? (
              <div className="mt-8">
                <EmptyState
                  title="No suppliers found."
                  description="The search ran but returned no supplier records. Try a broader query or different constraints."
                  action={
                    <Link to="/app/search">
                      <Button variant="secondary">New search</Button>
                    </Link>
                  }
                />
              </div>
            ) : (
              <div className="mt-8 grid gap-4">
                {data.suppliers.map((s, i) => {
                  const isSelected = selected.has(i);
                  const derivedId = searchId
                    ? `${searchId}--${i}`
                    : `s-${i}`;
                  return (
                    <div key={derivedId} className="relative">
                      <label
                        className="absolute left-4 top-4 z-10 flex items-center gap-2 cursor-pointer"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <input
                          type="checkbox"
                          checked={isSelected}
                          onChange={() => toggleSelect(i)}
                          className="h-4 w-4 accent-acc cursor-pointer"
                          aria-label={`Select ${s.company_name ?? 'supplier'} for comparison`}
                        />
                      </label>
                      <div className="pl-10">
                        <SupplierCard
                          supplier={s}
                          onClick={() =>
                            navigate(`/app/suppliers/${encodeURIComponent(derivedId)}`, {
                              state: { supplier: s, searchId },
                            })
                          }
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </>
        ) : null}
      </div>

      {selected.size >= 1 && data ? (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-40">
          <div className="flex items-center gap-4 rounded-full border border-acc/40 bg-ink/95 backdrop-blur px-5 py-3 shadow-lg">
            <span className="font-mono text-[10px] tracking-[.22em] text-acc/90">
              {selected.size} SELECTED
            </span>
            <Button
              variant="primary"
              disabled={selected.size < 2}
              onClick={goToCompare}
            >
              Compare
            </Button>
            <button
              type="button"
              onClick={() => setSelected(new Set())}
              className="font-mono text-[10px] tracking-[.22em] text-white/50 hover:text-white/80"
            >
              CLEAR
            </button>
          </div>
        </div>
      ) : null}
    </AppShell>
  );
}