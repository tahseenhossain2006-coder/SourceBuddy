import { ApiError } from '@/lib/errors';
import { Button } from './Button';

interface ErrorBannerProps {
  error: unknown;
  onRetry?: () => void;
}

function toUserMessage(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.status === 0) return 'Network error. Check your connection and try again.';
    if (error.status === 401) return 'Your session has expired. Please sign in again.';
    if (error.status === 403) return "You don't have permission to do that.";
    if (error.status === 404) return 'That resource was not found.';
    if (error.status === 422) return 'Some fields need attention.';
    if (error.status === 429) {
      return error.retryAfter
        ? `Too many requests. Try again in ${error.retryAfter}s.`
        : 'Too many requests. Try again shortly.';
    }
    if (error.status >= 500) return 'Something went wrong on our side. Please try again.';
    return error.message || 'Request failed.';
  }
  if (error instanceof Error) return error.message;
  return 'Something went wrong.';
}

export function ErrorBanner({ error, onRetry }: ErrorBannerProps) {
  return (
    <div
      role="alert"
      className="flex flex-col gap-3 rounded-2xl border border-[#ff7a66]/40 bg-[#ff7a66]/[.06] px-5 py-4 sm:flex-row sm:items-center sm:justify-between"
    >
      <p className="text-sm text-[#ffb1a3]">{toUserMessage(error)}</p>
      {onRetry ? (
        <Button variant="secondary" onClick={onRetry}>
          Retry
        </Button>
      ) : null}
    </div>
  );
}