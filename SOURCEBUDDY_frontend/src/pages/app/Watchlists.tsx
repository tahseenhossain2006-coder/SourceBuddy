import { useEffect, useState } from 'react';
import type { FormEvent } from 'react';
import { AppShell } from '@/layouts/AppShell';
import { Button } from '@/components/Button';
import { Input } from '@/components/Input';
import { EmptyState } from '@/components/EmptyState';
import { ErrorBanner } from '@/components/ErrorBanner';
import { Spinner } from '@/components/Spinner';
import { StatusBadge } from '@/components/StatusBadge';
import { createWatchlist, deleteWatchlist, listWatchlists, checkWatchlist } from '@/api/watchlists';
import type { Watchlist, WatchlistCheckResult, WatchType } from '@/types';

const WATCH_TYPES: WatchType[] = ['supplier', 'product', 'price', 'moq', 'rfq'];

export default function Watchlists() {
  const [items, setItems] = useState<Watchlist[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<unknown>(null);

  const [type, setType] = useState<WatchType>('supplier');
  const [targetId, setTargetId] = useState('');
  const [creating, setCreating] = useState(false);

  const [busyId, setBusyId] = useState<string | null>(null);
  const [lastCheck, setLastCheck] = useState<Record<string, WatchlistCheckResult>>({});

  async function refresh() {
    setLoading(true);
    setError(null);
    try {
      const list = await listWatchlists();
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

  async function handleCreate(e: FormEvent) {
    e.preventDefault();
    if (!targetId.trim()) return;
    setCreating(true);
    setError(null);
    try {
      await createWatchlist({ type, target_id: targetId.trim(), condition: null });
      setTargetId('');
      await refresh();
    } catch (err) {
      setError(err);
    } finally {
      setCreating(false);
    }
  }

  async function handleDelete(id: string) {
    setBusyId(id);
    setError(null);
    try {
      await deleteWatchlist(id);
      setItems((prev) => (prev ? prev.filter((w) => w.id !== id) : prev));
    } catch (err) {
      setError(err);
    } finally {
      setBusyId(null);
    }
  }

  async function handleCheck(id: string) {
    setBusyId(id);
    setError(null);
    try {
      const res = await checkWatchlist(id);
      setLastCheck((prev) => ({ ...prev, [id]: res }));
    } catch (err) {
      setError(err);
    } finally {
      setBusyId(null);
    }
  }

  return (
    <AppShell>
      <div className="max-w-4xl mx-auto">
        <p className="font-mono text-[11px] tracking-[.28em] uppercase text-acc/90">
          Watchlists
        </p>
        <h1 className="mt-3 font-display italic text-3xl sm:text-4xl text-white">
          Keep an eye on it.
        </h1>

        <form onSubmit={handleCreate} className="mt-8 flex flex-col gap-4 sm:flex-row sm:items-end">
          <div className="flex-1">
            <Input
              label="Target"
              required
              value={targetId}
              onChange={(e) => setTargetId(e.target.value)}
              placeholder="https://supplier.example.com/ or UUID"
              disabled={creating}
            />
          </div>
          <div className="flex flex-col gap-2">
            <label
              htmlFor="watch-type"
              className="font-mono text-[11px] uppercase tracking-[.18em] text-white/50"
            >
              Type
            </label>
            <select
              id="watch-type"
              value={type}
              onChange={(e) => setType(e.target.value as WatchType)}
              disabled={creating}
              className="rounded-full border border-white/15 bg-white/[.05] px-5 py-3.5 text-sm text-white focus:outline-none focus:border-acc/60"
            >
              {WATCH_TYPES.map((t) => (
                <option key={t} value={t} className="bg-ink text-white">
                  {t}
                </option>
              ))}
            </select>
          </div>
          <Button type="submit" loading={creating}>
            Add
          </Button>
        </form>

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
              title="No watchlists yet."
              description="Add a supplier URL, product ID, or other target above to start tracking it."
            />
          </div>
        ) : null}

        {!loading && items && items.length > 0 ? (
          <ul className="mt-8 flex flex-col gap-3">
            {items.map((w) => {
              const check = lastCheck[w.id];
              return (
                <li
                  key={w.id}
                  className="rounded-2xl border border-white/10 bg-white/[.02] p-5"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="min-w-0">
                      <div className="flex items-center gap-3">
                        <StatusBadge status={w.type} label={w.type.toUpperCase()} />
                        {w.last_checked ? (
                          <span className="font-mono text-[10px] tracking-[.18em] text-white/30">
                            CHECKED {new Date(w.last_checked).toLocaleString()}
                          </span>
                        ) : (
                          <span className="font-mono text-[10px] tracking-[.18em] text-white/30">
                            NEVER CHECKED
                          </span>
                        )}
                      </div>
                      <p className="mt-3 text-sm text-white/85 break-words">
                        {w.target_id}
                      </p>
                      {check ? (
                        <p className="mt-2 font-mono text-[10px] tracking-[.18em] text-white/50">
                          {check.changed ? 'CHANGED' : 'NO CHANGE'} ·{' '}
                          {check.alert_created ? 'ALERT CREATED' : 'NO ALERT'}
                          {check.error ? ` · ERROR: ${check.error}` : ''}
                        </p>
                      ) : null}
                    </div>
                    <div className="flex shrink-0 gap-2">
                      <Button
                        variant="secondary"
                        loading={busyId === w.id}
                        onClick={() => handleCheck(w.id)}
                      >
                        Check
                      </Button>
                      <Button
                        variant="ghost"
                        loading={busyId === w.id}
                        onClick={() => handleDelete(w.id)}
                      >
                        Remove
                      </Button>
                    </div>
                  </div>
                </li>
              );
            })}
          </ul>
        ) : null}
      </div>
    </AppShell>
  );
}