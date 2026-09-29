import { apiRequest, SEARCH_TIMEOUT_MS } from './client';
import type {
  SearchDetailResponse,
  SearchRequest,
  SearchResponse,
} from '@/types';

/**
 * POST /api/v1/search
 *
 * Searches can take 30-120 seconds. Timeout is set to 180 s.
 */
export function runSearch(body: SearchRequest): Promise<SearchResponse> {
  return apiRequest<SearchResponse>('/api/v1/search', {
    method: 'POST',
    body,
    timeoutMs: SEARCH_TIMEOUT_MS,
  });
}

/**
 * GET /api/v1/search/{search_id}
 *
 * Returns the reduced supplier schema. 404 means the search was
 * persisted but is not accessible to this user, OR it was never
 * persisted at all (contract §3).
 */
export function getSearch(searchId: string): Promise<SearchDetailResponse> {
  return apiRequest<SearchDetailResponse>(
    `/api/v1/search/${encodeURIComponent(searchId)}`,
  );
}