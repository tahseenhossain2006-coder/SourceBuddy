import type { FullSearchSupplier, ReducedSearchSupplier } from '@/types';

type SupplierInput = FullSearchSupplier | ReducedSearchSupplier;

interface SupplierCardProps {
  supplier: SupplierInput;
  className?: string;
  /** When provided, the card becomes clickable and calls this. */
  onClick?: () => void;
}

function isFullSupplier(s: SupplierInput): s is FullSearchSupplier {
  return 'supplier_name' in s || 'confidence' in s || 'source_urls' in s;
}

function nameOf(s: SupplierInput): string | null {
  if (isFullSupplier(s)) return s.supplier_name ?? s.company_name ?? null;
  return s.company_name;
}

function renderList(items: string[], max = 6): { shown: string[]; more: number } {
  const shown = items.slice(0, max);
  const more = Math.max(0, items.length - shown.length);
  return { shown, more };
}

function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex items-baseline gap-3">
      <span className="shrink-0 font-mono text-[10px] tracking-[.18em] text-white/35">
        {label}
      </span>
      <span className="min-w-0 text-sm text-white/80">{children}</span>
    </div>
  );
}

export function SupplierCard({ supplier, className = '', onClick }: SupplierCardProps) {
  const name = nameOf(supplier);
  const website = supplier.website;
  const country = supplier.country;
  const location = isFullSupplier(supplier)
    ? [supplier.city, supplier.state].filter(Boolean).join(', ') || null
    : supplier.location;

  const moq = supplier.moq;
  const price = supplier.price;
  const currency = supplier.currency;

  const full = isFullSupplier(supplier) ? supplier : null;

  const products = full?.products ?? [];
  const categories = full?.product_categories ?? [];
  const certifications = full?.certifications ?? [];
  const shippingRegions = full?.shipping_regions ?? [];

  const productsView = products.length ? renderList(products) : null;
  const categoriesView = categories.length ? renderList(categories, 4) : null;
  const certsView = certifications.length ? renderList(certifications, 4) : null;
  const regionsView = shippingRegions.length ? renderList(shippingRegions, 4) : null;

  const domain = full?.domain ?? null;
  const supplierType = full?.supplier_type ?? null;
  const manufacturerStatus = full?.manufacturer_status ?? null;
  const paymentTerms = full?.payment_terms ?? null;
  const email = full?.email ?? null;
  const phone = full?.phone ?? null;
  const whatsapp = full?.whatsapp ?? null;
  const yearsInBusiness = full?.years_in_business ?? null;
  const confidence = full?.confidence ?? null;
  const evidenceCount = full && full.evidence ? Object.keys(full.evidence).length : 0;

  const interactive = Boolean(onClick);

  const body = (
    <>
      <header className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <h3 className="truncate text-base font-medium text-white">
            {name ?? 'Unnamed supplier'}
          </h3>
          {domain ? (
            <p className="font-mono text-[10px] tracking-[.18em] text-white/35 mt-1">
              {domain.toUpperCase()}
            </p>
          ) : null}
        </div>
        {confidence !== null ? (
          <span className="shrink-0 rounded-full border border-acc/30 px-2 py-0.5 font-mono text-[10px] tracking-[.14em] text-acc/90">
            {Math.round(confidence * 100)}%
          </span>
        ) : null}
      </header>

      <div className="mt-4 flex flex-col gap-2.5">
        {website ? (
          <Row label="SITE">
            <a
              href={website}
              target="_blank"
              rel="noopener noreferrer"
              onClick={(e) => e.stopPropagation()}
              className="underline decoration-white/20 hover:decoration-acc break-all"
            >
              {website}
            </a>
          </Row>
        ) : null}
        {country ? <Row label="CTRY">{country}</Row> : null}
        {location ? <Row label="LOC">{location}</Row> : null}
        {supplierType ? <Row label="TYPE">{supplierType}</Row> : null}
        {manufacturerStatus ? <Row label="MFR">{manufacturerStatus}</Row> : null}
        {moq !== null && moq !== undefined ? <Row label="MOQ">{String(moq)}</Row> : null}
        {price !== null && price !== undefined ? (
          <Row label="PRICE">
            {currency ? `${currency} ` : ''}
            {String(price)}
          </Row>
        ) : null}
        {paymentTerms ? <Row label="TERMS">{paymentTerms}</Row> : null}
        {yearsInBusiness !== null ? <Row label="YRS">{String(yearsInBusiness)}</Row> : null}
        {email ? <Row label="EMAIL">{email}</Row> : null}
        {phone ? <Row label="PHONE">{phone}</Row> : null}
        {whatsapp ? <Row label="WA">{whatsapp}</Row> : null}
      </div>

      {categoriesView ? (
        <div className="mt-4">
          <p className="font-mono text-[10px] tracking-[.18em] text-white/35">CATEGORIES</p>
          <div className="mt-2 flex flex-wrap gap-1.5">
            {categoriesView.shown.map((c) => (
              <span key={c} className="rounded-full border border-white/10 px-2 py-0.5 text-[11px] text-white/70">
                {c}
              </span>
            ))}
            {categoriesView.more > 0 ? (
              <span className="text-[11px] text-white/35">+{categoriesView.more}</span>
            ) : null}
          </div>
        </div>
      ) : null}

      {productsView ? (
        <div className="mt-4">
          <p className="font-mono text-[10px] tracking-[.18em] text-white/35">PRODUCTS</p>
          <div className="mt-2 flex flex-wrap gap-1.5">
            {productsView.shown.map((p) => (
              <span key={p} className="rounded-full border border-white/10 px-2 py-0.5 text-[11px] text-white/70">
                {p}
              </span>
            ))}
            {productsView.more > 0 ? (
              <span className="text-[11px] text-white/35">+{productsView.more}</span>
            ) : null}
          </div>
        </div>
      ) : null}

      {certsView ? (
        <div className="mt-4">
          <p className="font-mono text-[10px] tracking-[.18em] text-white/35">CERTIFICATIONS</p>
          <div className="mt-2 flex flex-wrap gap-1.5">
            {certsView.shown.map((c) => (
              <span key={c} className="rounded-full border border-acc/25 px-2 py-0.5 text-[11px] text-acc/80">
                {c}
              </span>
            ))}
            {certsView.more > 0 ? (
              <span className="text-[11px] text-white/35">+{certsView.more}</span>
            ) : null}
          </div>
        </div>
      ) : null}

      {regionsView ? (
        <div className="mt-4">
          <p className="font-mono text-[10px] tracking-[.18em] text-white/35">SHIPS TO</p>
          <div className="mt-2 flex flex-wrap gap-1.5">
            {regionsView.shown.map((r) => (
              <span key={r} className="rounded-full border border-white/10 px-2 py-0.5 text-[11px] text-white/70">
                {r}
              </span>
            ))}
            {regionsView.more > 0 ? (
              <span className="text-[11px] text-white/35">+{regionsView.more}</span>
            ) : null}
          </div>
        </div>
      ) : null}

      {evidenceCount > 0 ? (
        <p className="mt-5 font-mono text-[10px] tracking-[.18em] text-white/30">
          {evidenceCount} EVIDENCE {evidenceCount === 1 ? 'ITEM' : 'ITEMS'}
        </p>
      ) : null}
    </>
  );

  if (interactive) {
    return (
      <button
        type="button"
        onClick={onClick}
        className={[
          'w-full text-left rounded-2xl border border-white/10 bg-white/[.02] p-5 transition-colors',
          'hover:border-acc/40 hover:bg-white/[.03] cursor-pointer',
          'focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-acc/60',
          className,
        ].join(' ')}
      >
        {body}
      </button>
    );
  }

  return (
    <article
      className={[
        'rounded-2xl border border-white/10 bg-white/[.02] p-5 transition-colors',
        'hover:border-white/20',
        className,
      ].join(' ')}
    >
      {body}
    </article>
  );
}