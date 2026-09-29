import { Link } from 'react-router-dom';
import { AppShell } from '@/layouts/AppShell';
import { useAuth } from '@/features/auth/useAuth';

interface Tile {
  to: string;
  title: string;
  description: string;
}

const TILES: Tile[] = [
  {
    to: '/app/search',
    title: 'New search',
    description: 'Describe a product once. Get back a ranked supplier shortlist.',
  },
  {
    to: '/app/watchlists',
    title: 'Watchlists',
    description: 'Track suppliers, prices, and MOQ changes. Get alerted when something moves.',
  },
  {
    to: '/app/alerts',
    title: 'Alerts',
    description: 'Unread alerts from the watchlist checks you have running.',
  },
  {
    to: '/app/rfq',
    title: 'RFQs',
    description: 'Create a request for quote and send it to selected suppliers.',
  },
];

export default function AppHome() {
  const { user } = useAuth();
  const name = user?.full_name ?? user?.email ?? null;

  return (
    <AppShell>
      <div className="max-w-5xl mx-auto">
        <p className="font-mono text-[11px] tracking-[.28em] uppercase text-acc/90">
          Console
        </p>
        <h1 className="mt-4 font-display italic text-4xl sm:text-5xl text-white">
          {name ? `Welcome back, ${name.split(' ')[0]}.` : 'Welcome back.'}
        </h1>
        <p className="mt-3 max-w-xl text-sm text-white/55 leading-relaxed">
          Start a search, review what you have already surfaced, or check what changed.
        </p>

        <div className="mt-10 grid gap-5 sm:grid-cols-2">
          {TILES.map((tile) => (
            <Link
              key={tile.to}
              to={tile.to}
              className="group rounded-2xl border border-white/10 bg-white/[.02] p-6 transition-colors hover:border-acc/40 hover:bg-white/[.04]"
            >
              <p className="font-mono text-[10px] tracking-[.22em] uppercase text-white/35">
                {tile.title}
              </p>
              <p className="mt-3 text-base text-white/85 leading-relaxed">
                {tile.description}
              </p>
              <p className="mt-4 font-mono text-[10px] tracking-[.22em] text-acc/70 group-hover:text-acc">
                Open →
              </p>
            </Link>
          ))}
        </div>
      </div>
    </AppShell>
  );
}