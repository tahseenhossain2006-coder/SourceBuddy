import { useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import './landing.css';
import { landingBody } from './landingBody';
import { initLandingPage } from './landing-scripts';
import { useAuth } from '@/features/auth/useAuth';

export default function Landing() {
  const hostRef = useRef<HTMLDivElement | null>(null);
  const navigate = useNavigate();
  const { status } = useAuth();

  // Install the landing-page scripts exactly as before.
  useEffect(() => {
    const cleanup = initLandingPage();
    return cleanup;
  }, []);

  // Intercept specific anchors and route them into the SPA.
  useEffect(() => {
    const host = hostRef.current;
    if (!host) return;

    const onClick = (e: MouseEvent) => {
      const target = e.target;
      if (!(target instanceof Element)) return;
      const anchor = target.closest('a');
      if (!anchor) return;
      const href = anchor.getAttribute('href');
      if (!href) return;

      // Account menu items: route to /login or /app based on auth state.
      const isAccountItem =
        anchor.classList.contains('pitem') ||
        anchor.getAttribute('role') === 'menuitem';

      if (isAccountItem) {
        e.preventDefault();
        e.stopPropagation();
        navigate(status === 'authenticated' ? '/app' : '/login');
        return;
      }

      // Nav + CTA anchors that must route instead of scroll.
      // Match by href and by the label text, so this survives minor HTML edits.
      const text = (anchor.textContent ?? '').trim().toLowerCase();

      const route =
        // Nav "Engine"
        (href === '#hero' && anchor.classList.contains('nav-link') && text === 'engine') ? '/app' :
        // "Start sourcing" primary CTA
        (text === 'start sourcing') ? '/app/search' :
        // "Get early access" CTA — everywhere it appears
        (text.startsWith('get early access')) ? '/signup' :
        null;

      if (route) {
        e.preventDefault();
        e.stopPropagation();
        navigate(route);
      }
    };

    host.addEventListener('click', onClick, true);
    return () => host.removeEventListener('click', onClick, true);
  }, [navigate, status]);

  return (
    <div
      ref={hostRef}
      className="bg-ink text-white antialiased font-sans tracking-[-0.02em] overflow-x-hidden"
      dangerouslySetInnerHTML={{ __html: landingBody }}
    />
  );
}