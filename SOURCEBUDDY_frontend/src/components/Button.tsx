import type { ButtonHTMLAttributes, ReactNode } from 'react';
import { Spinner } from './Spinner';

type Variant = 'primary' | 'secondary' | 'ghost' | 'danger';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  loading?: boolean;
  children: ReactNode;
}

const variantClasses: Record<Variant, string> = {
  primary:
    'bg-acc text-[#04231b] font-semibold hover:bg-[#7cf0d3] disabled:hover:bg-acc',
  secondary:
    'bg-white/5 text-white border border-white/15 hover:bg-white/10 hover:border-white/25',
  ghost:
    'bg-transparent text-white/75 hover:text-white hover:bg-white/5',
  danger:
    'bg-[#ff7a66] text-[#2b0d07] font-semibold hover:bg-[#ff9480]',
};

export function Button({
  variant = 'primary',
  loading = false,
  disabled,
  type = 'button',
  children,
  className = '',
  ...rest
}: ButtonProps) {
  const isDisabled = disabled || loading;
  return (
    <button
      type={type}
      disabled={isDisabled}
      aria-busy={loading || undefined}
      className={[
        'inline-flex items-center justify-center gap-2 rounded-full px-5 py-3 text-sm',
        'transition-colors duration-200',
        'disabled:opacity-50 disabled:cursor-not-allowed',
        'focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-[3px] focus-visible:outline-acc/60',
        variantClasses[variant],
        className,
      ].join(' ')}
      {...rest}
    >
      {loading ? <Spinner size="sm" /> : null}
      <span>{children}</span>
    </button>
  );
}