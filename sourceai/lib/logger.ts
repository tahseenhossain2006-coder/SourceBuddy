// lib/logger.ts
type LogLevel = 'info' | 'warn' | 'error' | 'debug';

export function log(level: LogLevel, message: string, meta?: Record<string, any>) {
  const timestamp = new Date().toISOString();
  const prefix = `[${timestamp}] [${level.toUpperCase()}]`;
  switch (level) {
    case 'info':
      console.info(prefix, message, meta || '');
      break;
    case 'warn':
      console.warn(prefix, message, meta || '');
      break;
    case 'error':
      console.error(prefix, message, meta || '');
      break;
    case 'debug':
      console.debug(prefix, message, meta || '');
      break;
    default:
      console.log(prefix, message, meta || '');
  }
}

export const logger = {
  info: (msg: string, meta?: any) => log('info', msg, meta),
  warn: (msg: string, meta?: any) => log('warn', msg, meta),
  error: (msg: string, meta?: any) => log('error', msg, meta),
  debug: (msg: string, meta?: any) => log('debug', msg, meta),
};