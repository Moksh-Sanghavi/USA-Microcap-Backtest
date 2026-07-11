// Shared number/currency formatting helpers so every panel renders financial
// data consistently (fixed decimals, thousands separators, monospaced-ready).

export function formatCurrency(value, { decimals = 2 } = {}) {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return value.toLocaleString("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

export function formatPercent(value, { decimals = 2, signed = true } = {}) {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  const sign = signed && value > 0 ? "+" : "";
  return `${sign}${value.toFixed(decimals)}%`;
}

export function formatNumber(value, { decimals = 2 } = {}) {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return value.toLocaleString("en-US", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

export function formatDate(value) {
  if (!value) return "—";
  return value; // API already returns ISO "YYYY-MM-DD" strings; pass through
}

/** Tailwind text color class for a signed financial value. */
export function pnlColorClass(value) {
  if (value === null || value === undefined || Number.isNaN(value)) return "text-slate-400";
  return value > 0 ? "text-emerald-400" : value < 0 ? "text-rose-400" : "text-slate-300";
}
