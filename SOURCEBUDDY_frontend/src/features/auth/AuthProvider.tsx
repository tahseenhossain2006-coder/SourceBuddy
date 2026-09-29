import { useCallback, useEffect, useMemo, useState } from 'react';
import type { ReactNode } from 'react';
import * as authApi from '@/api/auth';
import { ApiError } from '@/lib/errors';
import { clearTokens, getAccessToken, setTokens } from '@/lib/storage';
import { AuthContext } from './useAuth';
import type { AuthContextValue, AuthStatus } from './useAuth';
import type { User } from '@/types';

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [status, setStatus] = useState<AuthStatus>('loading');
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function bootstrap() {
      const token = getAccessToken();
      if (!token) {
        if (!cancelled) {
          setUser(null);
          setStatus('unauthenticated');
        }
        return;
      }
      try {
        const me = await authApi.me();
        if (!cancelled) {
          setUser(me);
          setStatus('authenticated');
        }
      } catch (err) {
        if (!cancelled) {
          if (err instanceof ApiError && err.status === 401) {
            clearTokens();
          }
          setUser(null);
          setStatus('unauthenticated');
        }
      }
    }

    void bootstrap();
    return () => {
      cancelled = true;
    };
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const tokens = await authApi.login({ email, password });
    setTokens({
      access: tokens.access_token,
      refresh: tokens.refresh_token,
    });
    const me = await authApi.me();
    setUser(me);
    setStatus('authenticated');
  }, []);

  const register = useCallback(
    async (email: string, password: string, fullName?: string | null) => {
      await authApi.register({
        email,
        password,
        full_name: fullName ?? null,
      });
      const tokens = await authApi.login({ email, password });
      setTokens({
        access: tokens.access_token,
        refresh: tokens.refresh_token,
      });
      const me = await authApi.me();
      setUser(me);
      setStatus('authenticated');
    },
    [],
  );

  const logout = useCallback(() => {
    clearTokens();
    setUser(null);
    setStatus('unauthenticated');
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({ status, user, login, register, logout }),
    [status, user, login, register, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}