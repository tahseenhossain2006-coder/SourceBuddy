import { useState } from 'react';
import type { FormEvent } from 'react';
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '@/features/auth/useAuth';
import PublicLayout from '../layouts/PublicLayout';
import { Button } from '@/components/Button';
import { Input } from '@/components/Input';
import { ErrorBanner } from '@/components/ErrorBanner';

interface LocationState {
  from?: { pathname?: string };
}

export default function Login() {
  const { status, login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const state = (location.state as LocationState | null) ?? null;

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<unknown>(null);

  if (status === 'authenticated') {
    const to = state?.from?.pathname ?? '/app';
    return <Navigate to={to} replace />;
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login(email, password);
      navigate(state?.from?.pathname ?? '/app', { replace: true });
    } catch (err) {
      setError(err);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <PublicLayout
      headerRight={
        <Link to="/signup" className="text-white/60 hover:text-white transition-colors">
          Need an account?
        </Link>
      }
    >
      <div className="w-full max-w-sm">
        <p className="font-mono text-[13px] tracking-[.28em] uppercase text-acc/90">
          Sign in
        </p>
        <h1 className="mt-4 font-display italic text-4xl text-white">
          Back aboard.
        </h1>
        <p className="mt-3 text-sm text-white/55 leading-relaxed">
          Access the sourcing console.
        </p>

        <form onSubmit={handleSubmit} className="mt-8 flex flex-col gap-5" noValidate>
          <Input
            label="Email"
            type="email"
            autoComplete="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@company.com"
            disabled={submitting}
          />
          <Input
            label="Password"
            type="password"
            autoComplete="current-password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••"
            disabled={submitting}
          />
          {error ? <ErrorBanner error={error} /> : null}
          <Button type="submit" loading={submitting}>
            Sign in
          </Button>
        </form>
      </div>
    </PublicLayout>
  );
}