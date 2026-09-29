import { useState } from 'react';
import type { FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { AppShell } from '@/layouts/AppShell';
import { Button } from '@/components/Button';
import { Input } from '@/components/Input';
import { ErrorBanner } from '@/components/ErrorBanner';
import { createRFQ } from '@/api/rfqs';

export default function RFQList() {
  const navigate = useNavigate();
  const [title, setTitle] = useState('');
  const [productName, setProductName] = useState('');
  const [quantity, setQuantity] = useState('');
  const [unit, setUnit] = useState('pcs');
  const [supplierIds, setSupplierIds] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<unknown>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);

    const parsedSuppliers = supplierIds
      .split(',')
      .map((s) => s.trim())
      .filter(Boolean);

    const parsedQuantity = Number(quantity);
    if (!Number.isFinite(parsedQuantity) || parsedQuantity <= 0) {
      setError(new Error('Quantity must be a positive number.'));
      return;
    }
    if (parsedSuppliers.length === 0) {
      setError(new Error('Provide at least one supplier ID (comma-separated).'));
      return;
    }

    setSubmitting(true);
    try {
      const rfq = await createRFQ({
        title,
        items: [
          {
            product_name: productName,
            quantity: parsedQuantity,
            unit,
          },
        ],
        suppliers: parsedSuppliers,
      });
      navigate(`/app/rfq/${encodeURIComponent(rfq.id)}`);
    } catch (err) {
      setError(err);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AppShell>
      <div className="max-w-2xl mx-auto">
        <p className="font-mono text-[11px] tracking-[.28em] uppercase text-acc/90">
          RFQs
        </p>
        <h1 className="mt-3 font-display italic text-3xl sm:text-4xl text-white">
          Create an RFQ.
        </h1>
        <p className="mt-3 text-sm text-white/55 leading-relaxed">
          Sends a request for quote to the suppliers you name. Listing existing RFQs is
          not exposed by the backend yet, so this page is create-only.
        </p>

        <form onSubmit={handleSubmit} className="mt-10 flex flex-col gap-5" noValidate>
          <Input
            label="Title"
            required
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Q4 Bottle Sourcing"
            disabled={submitting}
          />
          <Input
            label="Product name"
            required
            value={productName}
            onChange={(e) => setProductName(e.target.value)}
            placeholder="Stainless Steel Bottle"
            disabled={submitting}
          />
          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Quantity"
              required
              type="number"
              min={1}
              value={quantity}
              onChange={(e) => setQuantity(e.target.value)}
              disabled={submitting}
            />
            <Input
              label="Unit"
              required
              value={unit}
              onChange={(e) => setUnit(e.target.value)}
              disabled={submitting}
            />
          </div>
          <Input
            label="Supplier IDs"
            required
            value={supplierIds}
            onChange={(e) => setSupplierIds(e.target.value)}
            placeholder="uuid, uuid, uuid"
            helperText="Comma-separated supplier UUIDs"
            disabled={submitting}
          />
          {error ? <ErrorBanner error={error} /> : null}
          <div className="flex items-center gap-4">
            <Button type="submit" loading={submitting}>
              Create RFQ
            </Button>
            <p className="font-mono text-[10px] tracking-[.2em] text-white/35">
              CREATED AS DRAFT
            </p>
          </div>
        </form>
      </div>
    </AppShell>
  );
}