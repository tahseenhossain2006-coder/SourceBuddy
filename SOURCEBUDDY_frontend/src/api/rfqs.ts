import { apiRequest } from './client';
import type { RFQ, RFQCreate, RFQStatus } from '@/types';

/**
 * Backend: sourceai/rfq/routes.py
 *
 * Documented endpoints:
 *   POST  /api/v1/rfqs/
 *   GET   /api/v1/rfqs/{rfq_id}
 *   PATCH /api/v1/rfqs/{rfq_id}/status
 *
 * The PATCH endpoint takes the raw enum value in the body, not an object:
 *   body: "approved"
 *   Content-Type: application/json
 *
 * There is no list endpoint on the RFQ router. The only existing list is
 * GET /api/v1/outreach/, which returns RFQ data under a misleading prefix
 * because sourceai/outreach/routes.py contains RFQ handler code. The frontend
 * deliberately does not call it; see README limitations.
 */

export function createRFQ(body: RFQCreate): Promise<RFQ> {
  return apiRequest<RFQ>('/api/v1/rfqs/', {
    method: 'POST',
    body,
  });
}

export function getRFQ(rfqId: string): Promise<RFQ> {
  return apiRequest<RFQ>(
    `/api/v1/rfqs/${encodeURIComponent(rfqId)}`,
  );
}

export function updateRFQStatus(
  rfqId: string,
  status: RFQStatus,
): Promise<{ status: string }> {
  return apiRequest<{ status: string }>(
    `/api/v1/rfqs/${encodeURIComponent(rfqId)}/status`,
    {
      method: 'PATCH',
      // Raw enum value, not an object. This is what the backend expects.
      body: status,
    },
  );
}