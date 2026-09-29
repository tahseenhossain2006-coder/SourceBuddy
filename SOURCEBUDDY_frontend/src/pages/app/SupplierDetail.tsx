import { useState } from 'react';
import { Link, useLocation, useNavigate, useParams } from 'react-router-dom';
import { AppShell } from '@/layouts/AppShell';
import { Button } from '@/components/Button';
import { EmptyState } from '@/components/EmptyState';
import { ErrorBanner } from '@/components/ErrorBanner';
import { SupplierCard } from '@/components/SupplierCard';
import { createWatchlist } from '@/api/watchlists';
import type { FullSearchSupplier, ReducedSearchSupplier } from '@/types';

interface SupplierDetailState {
  supplier?: FullSearchSupplier | ReducedSearchSupplier;
  searchId?: string;
}

export default function SupplierDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  const state = (location.state as SupplierDetailState | null) ?? null;
  const supplier = state?.supplier ?? null;

  const [watching, setWatching] = useState(false);
  const [watchError, setWatchError] = useState<unknown>(null);
  const [watched, setWatched] = useState(false);

  async function handleAddToWatchlist() {
    if (!supplier) return;
    const targetId = supplier.website ?? id ?? '';
    if (!targetId) return;
    setWatching(true);
    setWatchError(null);
    try {
      await createWatchlist({
        type: 'supplier',
        target_id: targetId,
        condition: null,
      });
      setWatched(true);
    } catch (err) {
      setWatchError(err);
    } finally {
      setWatching(false);
    }
  }

  return (
    <AppShell>
      <div className="max-w-3xl mx-auto">
        <button
          type="button"
          onClick={() => navigate(-1)}
          className="font-mono text-[10px] tracking-[.22em] uppercase text-white/40 hover:text-white/70 transition-colors"
        >
          â† Back
        </button>

        <p className="mt-6 font-mono text-[11px] tracking-[.28em] uppercase text-acc/90">
          Supplier
        </p>

        {supplier ? (
          <>
            <h1 className="mt-3 font-display italic text-3xl sm:text-4xl text-white break-words">
              {supplier.company_name ?? 'Unnamed supplier'}
            </h1>
            <p className="mt-2 font-mono text-[10px] tracking-[.2em] text-white/30">
              ID {id ?? 'â€”'}
            </p>

            <div className="mt-6 flex flex-wrap gap-3">
              {supplier.website ? (
                <a
                  href={supplier.website}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <Button variant="primary">Visit website</Button>
                </a>
              ) : (
                <span className="font-mono text-[10px] tracking-[.2em] text-white/35">
                  WEBSITE NOT AVAILABLE
                </span>
              )}

              {watched ? (
                <Link to="/app/watchlists">
                  <Button variant="secondary">Go to watchlists</Button>
                </Link>
              ) : (
                <Button
                  variant="secondary"
                  loading={watching}
                  onClick={handleAddToWatchlist}
                  disabled={!supplier.website && !id}
                >
                  Add to watchlist
                </Button>
              )}
            </div>

            {watchError ? (
              <div className="mt-4">
                <ErrorBanner error={watchError} />
              </div>
            ) : null}

            {watched ? (
              <p className="mt-4 font-mono text-[10px] tracking-[.2em] text-acc/90">
                ADDED TO WATCHLIST
              </p>
            ) : null}

            <div className="mt-8">
              <SupplierCard supplier={supplier} />
            </div>

            {state?.searchId ? (
              <p className="mt-6 text-xs text-white/40">
                From search{' '}
                <button
                  type="button"
                  onClick={() =>
                    navigate(
                      `/app/search/${encodeURIComponent(state.searchId!)}`,
                    )
                  }
                  className="underline decoration-white/20 hover:decoration-acc"
                >
                  {state.searchId}
                </button>
                .
              </p>
            ) : null}
          </>
        ) : (
          <div className="mt-8">
            <EmptyState
              title="Supplier detail requires search context."
              description="The backend does not expose a supplier-by-id endpoint. Open a supplier from a search result to see its details."
              action={
                <Button variant="secondary" onClick={() => navigate('/app/search')}>
                  Go to search
                </Button>
              }
            />
          </div>
        )}
      </div>
    </AppShell>
  );
}
