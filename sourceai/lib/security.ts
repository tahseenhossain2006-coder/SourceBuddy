// lib/security.ts
import { URL } from 'url';

const BLOCKED_IP_RANGES = [
  /^127\./, /^10\./, /^172\.(1[6-9]|2[0-9]|3[0-1])\./, /^192\.168\./,
  /^0\./, /^169\.254\./, /^::1$/, /^fc00:/, /^fe80:/,
];
const BLOCKED_HOSTNAMES = ['localhost', 'metadata.google.internal', '169.254.169.254'];
const BLOCKED_PROTOCOLS = ['file:', 'javascript:', 'data:'];

export function isUrlSafe(urlString: string): boolean {
  let url: URL;
  try {
    url = new URL(urlString);
  } catch {
    return false;
  }

  // Protocol
  if (BLOCKED_PROTOCOLS.includes(url.protocol)) return false;

  // Hostname
  const hostname = url.hostname.toLowerCase();
  if (BLOCKED_HOSTNAMES.includes(hostname)) return false;

  // IP ranges
  try {
    const ip = hostname; // might be hostname or IP
    for (const pattern of BLOCKED_IP_RANGES) {
      if (pattern.test(ip)) return false;
    }
  } catch {
    // ignore
  }

  return true;
}