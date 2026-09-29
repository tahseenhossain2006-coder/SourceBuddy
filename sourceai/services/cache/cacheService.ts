// services/cache/cacheService.ts
import { createClient } from '@supabase/supabase-js';
import { logger } from '@/lib/logger';

const SUPABASE_URL = process.env.SUPABASE_URL;
const SUPABASE_ANON_KEY = process.env.SUPABASE_ANON_KEY;
const supabase = SUPABASE_URL && SUPABASE_ANON_KEY
  ? createClient(SUPABASE_URL, SUPABASE_ANON_KEY)
  : null;

export async function getCache(key: string): Promise<any> {
  if (!supabase) return null;
  try {
    const { data } = await supabase
      .from('search_cache')
      .select('result_data')
      .eq('query', key)
      .maybeSingle();
    return data?.result_data || null;
  } catch (e) {
    logger.warn('Cache read failed', { key, error: e.message });
    return null;
  }
}

export async function setCache(key: string, data: any): Promise<void> {
  if (!supabase) return;
  try {
    await supabase.from('search_cache').upsert({
      query: key,
      result_data: data,
      expires_at: new Date(Date.now() + 86400000).toISOString(),
    });
  } catch (e) {
    logger.warn('Cache write failed', { key, error: e.message });
  }
}