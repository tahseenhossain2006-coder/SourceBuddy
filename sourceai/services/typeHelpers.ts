// services/typeHelpers.ts

/** Safely convert any value to a number, using 0 as fallback */
export function safeNumber(value: unknown): number {
  if (typeof value === 'number' && Number.isFinite(value)) return value;
  if (typeof value === 'string') {
    const trimmed = value.trim();
    if (trimmed === '') return 0;
    const parsed = Number(trimmed.replace(/,/g, ''));
    return Number.isFinite(parsed) ? parsed : 0;
  }
  return 0;
}

/** Safely compare two nullable numbers – returns false if either is null/undefined */
export function safeCompare(a: number | null | undefined, b: number | null | undefined): boolean {
  if (a == null || b == null) return false;
  return a > b;
}