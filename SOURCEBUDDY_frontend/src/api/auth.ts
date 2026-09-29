import { apiRequest } from './client';
import type {
  RefreshRequest,
  TokenResponse,
  User,
  UserCreate,
  UserLogin,
} from '@/types';

export function register(body: UserCreate): Promise<User> {
  return apiRequest<User>('/auth/register', {
    method: 'POST',
    body,
    skipAuth: true,
  });
}

export function login(body: UserLogin): Promise<TokenResponse> {
  return apiRequest<TokenResponse>('/auth/login', {
    method: 'POST',
    body,
    skipAuth: true,
  });
}

export function refresh(body: RefreshRequest): Promise<TokenResponse> {
  return apiRequest<TokenResponse>('/auth/refresh', {
    method: 'POST',
    body,
    skipAuth: true,
  });
}

export function me(): Promise<User> {
  return apiRequest<User>('/auth/me');
}