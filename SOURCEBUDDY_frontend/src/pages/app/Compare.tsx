import { useLocation, useNavigate } from 'react-router-dom';
import { AppShell } from '@/layouts/AppShell';
import { Button } from '@/components/Button';
import { EmptyState } from '@/components/EmptyState';
import type { FullSearchSupplier, ReducedSearchSupplier } from '@/types';

interface CompareState {
  suppliers?: Array<FullSearchSupplier | ReducedSearchSupplier>;
  query?: string;
}

type CellValue = string | number | null;

export default function Compare() {
  const navigate = useNavigate();
  const location = useLocation();
  const state = (location.state as CompareState | null) ?? null;
  const suppliers = state?.suppliers ?? [];

  if (suppliers.length < 2) {
    return (
      <AppShell>
        <div className="max-w-3xl mx-auto">
          <p className="font-mono text-[11px] tracking-[.28em] uppercase text-acc/90">
            Compare
          </p>
          <div className="mt-8">
            <EmptyState
              title="Nothing to compare yet."
              description="Comparison runs client-side over suppliers from a search result. Open a search, then choose two or more suppliers to compare."
              action={
                <Button variant="secondary" onClick={() => navigate('/app/search')}>
                  Go to search
                </Button>
              }
            />
          </div>
        </div>
      </AppShell>
    );
  }

  const rows: ReadonlyArray<readonly [string, (s: any) => CellValue]> = [
    ['Website', (s: any): CellValue => s.website ?? null],
    ['Country', (s: any): CellValue => s.country ?? null],
    [
      'Location',
      (s: any): CellValue => {
        if (s.location) return s.location;
        const parts = [s.city, s.state].filter(Boolean) as string[];
        return parts.length ? parts.join(', ') : null;
      },
    ],
    ['MOQ', (s: any): CellValue => s.moq ?? null],
    ['Price', (s: any): CellValue => s.price ?? null],
    ['Currency', (s: any): CellValue => s.currency ?? null],
  ];

  return (
    <AppShell>
      <div className="max-w-6xl mx-auto">
        <button
          type="button"
          onClick={() => navigate(-1)}
          className="font-mono text-[10px] tracking-[.22em] uppercase text-white/40 hover:text-white/70 transition-colors"
        >
          ← Back
        </button>
        <p className="mt-6 font-mono text-[11px] tracking-[.28em] uppercase text-acc/90">
          Compare
        </p>
        <h1 className="mt-3 font-display italic text-3xl sm:text-4xl text-white">
          Side by side.
        </h1>
        <p className="mt-2 text-xs text-white/40">
          Comparison is computed in the browser. No compare endpoint exists on the backend.
        </p>

        <div className="mt-8 overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead>
              <tr className="text-left text-white/40 font-mono text-[10px] tracking-[.18em] uppercase">
                <th className="px-4 py-3">Field</th>
                {suppliers.map((s, i) => (
                  <th key={i} className="px-4 py-3 text-white/80">
                    {s.company_name ?? `Supplier ${i + 1}`}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map(([label, get]) => (
                <tr key={label} className="border-t border-white/5">
                  <td className="px-4 py-3 font-mono text-[10px] tracking-[.18em] text-white/40">
                    {label}
                  </td>
                  {suppliers.map((s, i) => {
                    const v = get(s);
                    return (
                      <td key={i} className="px-4 py-3 text-white/80 break-words">
                        {v === null || v === undefined || v === '' ? (
                          <span className="text-white/25">—</span>
                        ) : (
                          String(v)
                        )}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </AppShell>
  );
}