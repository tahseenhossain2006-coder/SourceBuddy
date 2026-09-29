import type { ReactNode } from 'react';
import { Link } from 'react-router-dom';

interface PublicLayoutProps {
  children: ReactNode;
  /** Optional right-aligned header content (e.g. "Already have an account? Log in"). */
  headerRight?: ReactNode;
  /** If true, content is vertically centered. Default true. */
  centered?: boolean;
}

export function PublicLayout({
  children,
  headerRight,
  centered = true,
}: PublicLayoutProps) {
  return (
    <div className="min-h-screen flex flex-col bg-ink text-white">
      <header className="flex items-center justify-between px-6 py-5 sm:px-10">
        <Link
          to="/"
          className="font-mono text-[11px] uppercase tracking-[.28em] text-acc/90 hover:text-acc"
        >
          SourceBuddy
        </Link>
        {headerRight ? <div className="text-sm">{headerRight}</div> : null}
      </header>

      <main
        className={
          centered
            ? 'flex-1 grid place-items-center px-6 pb-16'
            : 'flex-1 px-6 pb-16'
        }
      >
        {children}
      </main>

      <footer className="px-6 py-5 sm:px-10">
        <p className="font-mono text-[10px] uppercase tracking-[.28em] text-white/25">
          © {new Date().getFullYear()} SourceBuddy
        </p>
      </footer>
    </div>
  );
}
export default PublicLayout;