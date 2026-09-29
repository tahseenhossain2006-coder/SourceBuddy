// services/agent/supplierFilter.ts
import { Supplier, Requirement } from '@/lib/types';

export function applyFilters(suppliers: Supplier[], requirements: Requirement): Supplier[] {
  let filtered = suppliers;
  // MOQ: if requirement has quantity, filter suppliers with MOQ <= quantity, but keep those with null MOQ (unknown)
  if (requirements.quantity) {
    filtered = filtered.filter(s => s.moq === null || s.moq <= requirements.quantity!);
  }
  // Budget: if budget_per_unit, filter suppliers with price_min <= budget, but keep null price_min
  if (requirements.budget_per_unit) {
    filtered = filtered.filter(s => s.price_min === null || s.price_min <= requirements.budget_per_unit!);
  }
  // Country
  if (requirements.target_country) {
    const countryLower = requirements.target_country.toLowerCase();
    filtered = filtered.filter(s =>
      s.country?.toLowerCase().includes(countryLower) ||
      s.region?.toLowerCase().includes(countryLower) ||
      s.city?.toLowerCase().includes(countryLower)
    );
  }
  // Customization
  if (requirements.customization_required === true) {
    filtered = filtered.filter(s => s.customization_available === true);
  }
  // If filtering results in empty, return original (fallback)
  return filtered.length > 0 ? filtered : suppliers;
}