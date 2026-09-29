import { useState } from 'react';
import type { FormEvent } from 'react';
import { Link, Navigate, useNavigate } from 'react-router-dom';
import { useAuth } from '@/features/auth/useAuth';
import PublicLayout from '@/layouts/PublicLayout';
import { Button } from '@/components/Button';
import { Input } from '@/components/Input';
import { ErrorBanner } from '@/components/ErrorBanner';

export default function Signup() {
  const { status, register } = useAuth();
  const navigate = useNavigate();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<unknown>(null);

  if (status === 'authenticated') {
    return <Navigate to="/app" replace />;
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await register(email, password, fullName || null);
      navigate('/app', { replace: true });
    } catch (err) {
      setError(err);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <PublicLayout
      headerRight={
        <Link to="/login" className="text-white/60 hover:text-white transition-colors">
          Already have an account?
        </Link>
      }
    >
      <div className="w-full max-w-sm">
        <p className="font-mono text-[11px] tracking-[.28em] uppercase text-acc/90">
          Create account
        </p>
        <h1 className="mt-4 font-display italic text-4xl text-white">
          Come aboard.
        </h1>
        <p className="mt-3 text-sm text-white/55 leading-relaxed">
          Start sourcing in a minute.
        </p>

        <form onSubmit={handleSubmit} className="mt-8 flex flex-col gap-5" noValidate>
          <Input
            label="Full name"
            type="text"
            autoComplete="name"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            placeholder="Optional"
            helperText="Optional"
            disabled={submitting}
          />
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
            autoComplete="new-password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="At least 8 characters"
            helperText="Minimum 8 characters"
            disabled={submitting}
          />
          {error ? <ErrorBanner error={error} /> : null}
          <Button type="submit" loading={submitting}>
            Create account
          </Button>
        </form>
      </div>
    </PublicLayout>
  );
}