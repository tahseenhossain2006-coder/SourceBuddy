import { useEffect, useState } from 'react';
import { AppShell } from '@/layouts/AppShell';
import { Button } from '@/components/Button';
import { EmptyState } from '@/components/EmptyState';
import { ErrorBanner } from '@/components/ErrorBanner';
import { Spinner } from '@/components/Spinner';
import { StatusBadge } from '@/components/StatusBadge';
import { listUnreadAlerts, markAlertRead } from '@/api/alerts';
import type { Alert } from '@/types';

export default function Alerts() {
  const [items, setItems] = useState<Alert[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<unknown>(null);
  const [busyId, setBusyId] = useState<string | null>(null);

  async function refresh() {
    setLoading(true);
    setError(null);
    try {
      const list = await listUnreadAlerts();
      setItems(list);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void refresh();
  }, []);

  async function handleMarkRead(id: string) {
    setBusyId(id);
    setError(null);
    try {
      await markAlertRead(id);
      // Backend list only returns unread, so removing locally matches server state.
      setItems((prev) => (prev ? prev.filter((a) => a.id !== id) : prev));
    } catch (err) {
      setError(err);
    } finally {
      setBusyId(null);
    }
  }

  return (
    <AppShell>
      <div className="max-w-3xl mx-auto">
        <p className="font-mono text-[11px] tracking-[.28em] uppercase text-acc/90">
          Alerts
        </p>
        <h1 className="mt-3 font-display italic text-3xl sm:text-4xl text-white">
          What changed.
        </h1>
        <p className="mt-3 text-sm text-white/55 leading-relaxed">
          Only unread alerts are shown. Marking an alert as read removes it from this list.
        </p>

        {error ? (
          <div className="mt-6">
            <ErrorBanner error={error} onRetry={refresh} />
          </div>
        ) : null}

        {loading ? (
          <div className="mt-10 flex justify-center">
            <Spinner size="lg" />
          </div>
        ) : null}

        {!loading && items && items.length === 0 ? (
          <div className="mt-8">
            <EmptyState
              title="No unread alerts."
              description="Watchlist checks will surface changes here."
            />
          </div>
        ) : null}

        {!loading && items && items.length > 0 ? (
          <ul className="mt-8 flex flex-col gap-3">
            {items.map((a) => (
              <li
                key={a.id}
                className="rounded-2xl border border-white/10 bg-white/[.02] p-5"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="min-w-0">
                    <div className="flex items-center gap-3">
                      <StatusBadge status={a.type} label={a.type.replace(/_/g, ' ').toUpperCase()} />
                      <span className="font-mono text-[10px] tracking-[.18em] text-white/30">
                        {new Date(a.created_at).toLocaleString()}
                      </span>
                    </div>
                    <p className="mt-3 text-sm text-white/85 break-words">{a.message}</p>
                  </div>
                  <Button
                    variant="secondary"
                    loading={busyId === a.id}
                    onClick={() => handleMarkRead(a.id)}
                  >
                    Mark read
                  </Button>
                </div>
              </li>
            ))}
          </ul>
        ) : null}
      </div>
    </AppShell>
  );
}