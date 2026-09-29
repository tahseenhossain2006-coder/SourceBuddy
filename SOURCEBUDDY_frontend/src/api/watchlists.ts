import { apiRequest } from './client';
import type {
  Watchlist,
  WatchlistCheckResult,
  WatchlistCreate,
} from '@/types';

/**
 * Backend: sourceai/watchlists/routes.py
 *
 * Documented endpoints:
 *   POST   /api/v1/watchlists/
 *   GET    /api/v1/watchlists/
 *   DELETE /api/v1/watchlists/{watch_id}
 *   POST   /api/v1/watchlists/{watch_id}/check
 *
 * Not implemented by the backend: get-one, update, add-supplier, remove-supplier.
 * Do not call them; they will 404 or 405.
 */

export function listWatchlists(): Promise<Watchlist[]> {
  return apiRequest<Watchlist[]>('/api/v1/watchlists/');
}

export function createWatchlist(body: WatchlistCreate): Promise<Watchlist> {
  return apiRequest<Watchlist>('/api/v1/watchlists/', {
    method: 'POST',
    body,
  });
}

export function deleteWatchlist(watchId: string): Promise<{ status: string }> {
  return apiRequest<{ status: string }>(
    `/api/v1/watchlists/${encodeURIComponent(watchId)}`,
    { method: 'DELETE' },
  );
}

export function checkWatchlist(watchId: string): Promise<WatchlistCheckResult> {
  return apiRequest<WatchlistCheckResult>(
    `/api/v1/watchlists/${encodeURIComponent(watchId)}/check`,
    { method: 'POST' },
  );
}