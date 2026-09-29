import { useState } from 'react';
import type { ReactNode } from 'react';
import { Link, NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '@/features/auth/useAuth';

interface AppShellProps {
  children: ReactNode;
  actions?: ReactNode;
}

const navItems = [
  { to: '/app', label: 'Home' },
  { to: '/app/search', label: 'Search' },
  { to: '/app/watchlists', label: 'Watchlists' },
  { to: '/app/alerts', label: 'Alerts' },
  { to: '/app/rfq', label: 'RFQs' },
];

export function AppShell({ children, actions }: AppShellProps) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [menuOpen, setMenuOpen] = useState(false);

  function handleLogout() {
    logout();
    navigate('/login', { replace: true });
  }

  return (
    <div className="min-h-screen flex flex-col bg-ink text-white">
      <header className="border-b border-white/5">
        <div className="flex items-center gap-6 px-6 py-4 sm:px-10">
          <Link
            to="/app"
            className="font-mono text-[11px] uppercase tracking-[.28em] text-acc/90 hover:text-acc"
          >
            SourceBuddy
          </Link>

          <nav className="flex items-center gap-5">
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === '/app'}
                className={({ isActive }) =>
                  [
                    'font-mono text-[11px] uppercase tracking-[.22em] transition-colors',
                    isActive
                      ? 'text-acc'
                      : 'text-white/45 hover:text-white/80',
                  ].join(' ')
                }
              >
                {item.label}
              </NavLink>
            ))}
          </nav>

          <div className="ml-auto flex items-center gap-4">
            {actions}
            <div className="relative">
              <button
                type="button"
                onClick={() => setMenuOpen((v) => !v)}
                aria-haspopup="menu"
                aria-expanded={menuOpen}
                className="font-mono text-[11px] uppercase tracking-[.22em] text-white/60 hover:text-white/90"
              >
                {user?.email ?? 'Account'}
              </button>
              {menuOpen ? (
                <div
                  role="menu"
                  className="absolute right-0 top-full mt-2 w-48 rounded border border-white/10 bg-ink/95 backdrop-blur p-1 shadow-lg z-20"
                >
                  <button
                    type="button"
                    role="menuitem"
                    onClick={handleLogout}
                    className="w-full text-left px-3 py-2 text-sm text-white/75 hover:bg-white/5 rounded"
                  >
                    Log out
                  </button>
                </div>
              ) : null}
            </div>
          </div>
        </div>
      </header>

      <main className="flex-1 px-6 py-8 sm:px-10">{children}</main>
    </div>
  );
}