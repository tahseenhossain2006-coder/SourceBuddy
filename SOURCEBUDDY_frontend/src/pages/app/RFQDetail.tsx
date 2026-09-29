import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { AppShell } from '@/layouts/AppShell';
import { Button } from '@/components/Button';
import { EmptyState } from '@/components/EmptyState';
import { ErrorBanner } from '@/components/ErrorBanner';
import { Spinner } from '@/components/Spinner';
import { StatusBadge } from '@/components/StatusBadge';
import { getRFQ, updateRFQStatus } from '@/api/rfqs';
import { ApiError } from '@/lib/errors';
import { RFQ_TRANSITIONS } from '@/types';
import type { RFQ, RFQStatus } from '@/types';

export default function RFQDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [rfq, setRfq] = useState<RFQ | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<unknown>(null);
  const [notFound, setNotFound] = useState(false);
  const [updating, setUpdating] = useState<RFQStatus | null>(null);

  useEffect(() => {
    if (!id) return;
    let cancelled = false;
    setLoading(true);
    setError(null);
    setNotFound(false);

    (async () => {
      try {
        const data = await getRFQ(id);
        if (!cancelled) setRfq(data);
      } catch (err) {
        if (cancelled) return;
        if (err instanceof ApiError && err.status === 404) setNotFound(true);
        else setError(err);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [id]);

  async function transition(next: RFQStatus) {
    if (!id || !rfq) return;
    setUpdating(next);
    setError(null);
    try {
      await updateRFQStatus(id, next);
      const fresh = await getRFQ(id);
      setRfq(fresh);
    } catch (err) {
      setError(err);
    } finally {
      setUpdating(null);
    }
  }

  return (
    <AppShell>
      <div className="max-w-3xl mx-auto">
        <button
          type="button"
          onClick={() => navigate('/app/rfq')}
          className="font-mono text-[10px] tracking-[.22em] uppercase text-white/40 hover:text-white/70 transition-colors"
        >
          ← RFQs
        </button>

        {loading ? (
          <div className="mt-10 flex justify-center">
            <Spinner size="lg" />
          </div>
        ) : null}

        {error ? (
          <div className="mt-8">
            <ErrorBanner error={error} onRetry={() => { setError(null); setLoading(true); }} />
          </div>
        ) : null}

        {notFound ? (
          <div className="mt-8">
            <EmptyState
              title="RFQ not found."
              description="It may have been deleted, or the ID does not belong to your account."
              action={
                <Button variant="secondary" onClick={() => navigate('/app/rfq')}>
                  Back to RFQs
                </Button>
              }
            />
          </div>
        ) : null}

        {rfq ? (
          <>
            <div className="mt-6 flex items-center gap-4">
              <StatusBadge status={rfq.status} />
              <p className="font-mono text-[10px] tracking-[.2em] text-white/30">
                {rfq.id}
              </p>
            </div>
            <h1 className="mt-4 font-display italic text-3xl sm:text-4xl text-white break-words">
              {rfq.title}
            </h1>

            <dl className="mt-8 grid grid-cols-2 gap-4 text-sm sm:grid-cols-3">
              <div>
                <dt className="font-mono text-[10px] tracking-[.18em] text-white/35">
                  CREATED
                </dt>
                <dd className="mt-1 text-white/80">
                  {new Date(rfq.created_at).toLocaleString()}
                </dd>
              </div>
              <div>
                <dt className="font-mono text-[10px] tracking-[.18em] text-white/35">
                  SUPPLIERS
                </dt>
                <dd className="mt-1 text-white/80">{rfq.suppliers.length}</dd>
              </div>
              <div>
                <dt className="font-mono text-[10px] tracking-[.18em] text-white/35">
                  ITEMS
                </dt>
                <dd className="mt-1 text-white/80">{rfq.items.length}</dd>
              </div>
            </dl>

            <div className="mt-10">
              <p className="font-mono text-[10px] tracking-[.18em] text-white/35 uppercase">
                Items
              </p>
              <ul className="mt-3 flex flex-col gap-2">
                {rfq.items.map((it, i) => (
                  <li
                    key={i}
                    className="rounded-xl border border-white/10 bg-white/[.02] px-4 py-3 text-sm text-white/85"
                  >
                    {it.product_name} — {it.quantity} {it.unit}
                  </li>
                ))}
              </ul>
            </div>

            <div className="mt-10">
              <p className="font-mono text-[10px] tracking-[.18em] text-white/35 uppercase">
                Transitions
              </p>
              {(RFQ_TRANSITIONS[rfq.status] ?? []).length === 0 ? (
                <p className="mt-3 text-xs text-white/40">
                  This RFQ is in a terminal state. No further transitions are available.
                </p>
              ) : (
                <div className="mt-3 flex flex-wrap gap-3">
                  {(RFQ_TRANSITIONS[rfq.status] ?? []).map((next) => (
                    <Button
                      key={next}
                      variant={next === 'cancelled' ? 'danger' : 'secondary'}
                      loading={updating === next}
                      onClick={() => transition(next)}
                    >
                      {next.replace(/_/g, ' ')}
                    </Button>
                  ))}
                </div>
              )}
            </div>
          </>
        ) : null}
      </div>
    </AppShell>
  );
}