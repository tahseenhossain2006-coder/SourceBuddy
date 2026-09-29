import type { ReactNode } from 'react';

interface EmptyStateProps {
  title: string;
  description?: string;
  action?: ReactNode;
}

export function EmptyState({ title, description, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center rounded-3xl border border-white/10 bg-white/[.02] px-6 py-16 text-center">
      <p className="font-display italic text-2xl text-white/85">{title}</p>
      {description ? (
        <p className="mt-3 max-w-md text-sm text-white/55 leading-relaxed">{description}</p>
      ) : null}
      {action ? <div className="mt-6">{action}</div> : null}
    </div>
  );
}