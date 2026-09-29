export type StatusKind =
  | 'draft'
  | 'approved'
  | 'sending'
  | 'sent'
  | 'waiting'
  | 'partial_response'
  | 'completed'
  | 'cancelled'
  | 'loading'
  | 'success'
  | 'error'
  | 'unread'
  | 'read';

interface StatusBadgeProps {
  status: StatusKind | string;
  label?: string;
}

const STYLES: Record<string, string> = {
  draft: 'border-white/15 text-white/60',
  approved: 'border-acc/40 text-acc',
  sending: 'border-acc/40 text-acc',
  sent: 'border-acc/30 text-acc/90',
  waiting: 'border-white/20 text-white/70',
  partial_response: 'border-[#ffd479]/40 text-[#ffd479]',
  completed: 'border-acc/50 text-acc',
  cancelled: 'border-white/10 text-white/35',
  loading: 'border-acc/40 text-acc',
  success: 'border-acc/50 text-acc',
  error: 'border-[#ff7a66]/50 text-[#ff7a66]',
  unread: 'border-acc/50 text-acc',
  read: 'border-white/15 text-white/50',
};

const LABELS: Record<string, string> = {
  partial_response: 'PARTIAL',
};

export function StatusBadge({ status, label }: StatusBadgeProps) {
  const style = STYLES[status] ?? 'border-white/15 text-white/60';
  const text = label ?? LABELS[status] ?? status.replace(/_/g, ' ').toUpperCase();
  return (
    <span
      className={[
        'inline-flex items-center rounded-full border px-2.5 py-1',
        'font-mono text-[10px] tracking-[.16em]',
        style,
      ].join(' ')}
    >
      {text}
    </span>
  );
}