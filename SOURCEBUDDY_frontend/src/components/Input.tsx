import { useId } from 'react';
import type { InputHTMLAttributes } from 'react';

interface InputProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'id'> {
  label: string;
  error?: string | null;
  helperText?: string;
  required?: boolean;
}

export function Input({
  label,
  error,
  helperText,
  required,
  className = '',
  ...rest
}: InputProps) {
  const id = useId();
  const errorId = error ? `${id}-error` : undefined;
  const helperId = helperText ? `${id}-helper` : undefined;
  const describedBy = [errorId, helperId].filter(Boolean).join(' ') || undefined;

  return (
    <div className="flex flex-col gap-2">
      <label
        htmlFor={id}
        className="font-mono text-[11px] uppercase tracking-[.18em] text-white/50"
      >
        {label}
        {required ? <span className="text-acc/80 ml-1">*</span> : null}
      </label>
      <input
        id={id}
        required={required}
        aria-invalid={error ? true : undefined}
        aria-describedby={describedBy}
        className={[
          'w-full rounded-full border bg-white/[.05] px-5 py-3.5 text-sm text-white',
          'placeholder:text-white/25',
          'transition-colors duration-200',
          'focus:outline-none focus:bg-white/[.08]',
          error
            ? 'border-[#ff7a66]/60 focus:border-[#ff7a66]'
            : 'border-white/15 focus:border-acc/60',
          className,
        ].join(' ')}
        {...rest}
      />
      {error ? (
        <p id={errorId} className="text-xs text-[#ff7a66]">
          {error}
        </p>
      ) : null}
      {helperText && !error ? (
        <p id={helperId} className="font-mono text-[10px] tracking-[.18em] text-white/35">
          {helperText}
        </p>
      ) : null}
    </div>
  );
}