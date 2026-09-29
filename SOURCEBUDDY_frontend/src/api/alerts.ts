import { apiRequest } from './client';
import type { Alert } from '@/types';

/**
 * Backend: sourceai/alerts/routes.py
 *
 * Documented endpoints:
 *   GET  /api/v1/alerts/                 — unread only, newest first
 *   POST /api/v1/alerts/{alert_id}/read
 *
 * Backend does not expose: read-alerts list, bulk mark-read, delete, create.
 */

export function listUnreadAlerts(): Promise<Alert[]> {
  return apiRequest<Alert[]>('/api/v1/alerts/');
}

export function markAlertRead(alertId: string): Promise<{ status: string }> {
  return apiRequest<{ status: string }>(
    `/api/v1/alerts/${encodeURIComponent(alertId)}/read`,
    { method: 'POST' },
  );
}