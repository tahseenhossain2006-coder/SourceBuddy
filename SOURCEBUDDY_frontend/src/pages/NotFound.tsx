import { Link } from 'react-router-dom';

export default function NotFound() {
  return (
    <div className="min-h-screen grid place-items-center">
      <div className="text-center">
        <p className="font-mono text-[11px] uppercase tracking-[.28em] text-white/40">
          404
        </p>
        <p className="mt-3 text-white/60 text-sm">Page not found</p>
        <Link to="/" className="mt-6 inline-block text-white/80 text-sm underline">
          Go home
        </Link>
      </div>
    </div>
  );
}