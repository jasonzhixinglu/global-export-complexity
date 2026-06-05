// Display helpers.
export function fmtPct(x, dp = 1) {
  if (x == null || !isFinite(x)) return '—'
  return (x * 100).toFixed(dp) + '%'
}

export function fmtB(x, dp = 1) {
  if (x == null || !isFinite(x)) return '—'
  if (Math.abs(x) >= 1000) return '$' + (x / 1000).toFixed(dp) + 'T'
  return '$' + x.toFixed(dp) + 'B'
}

export function fmtPci(x) {
  if (x == null || !isFinite(x)) return '—'
  return (x >= 0 ? '+' : '') + x.toFixed(2)
}

// Categorical palette — saturated and vivid (not pastel), readable on dark.
// First four are the defaults (CHN / USA / DEU / JPN): blue / red / green / amber.
export const PALETTE = [
  '#2563eb', '#dc2626', '#16a34a', '#d97706', '#7c3aed',
  '#0891b2', '#db2777', '#65a30d', '#ea580c', '#4f46e5',
  '#0d9488', '#ca8a04', '#e11d48', '#0284c7', '#15803d',
  '#9333ea', '#c2410c', '#be185d', '#047857', '#b45309',
  '#1d4ed8', '#b91c1c', '#4d7c0f', '#a21caf', '#0369a1',
  '#7e22ce', '#dc2626', '#059669', '#d97706', '#6d28d9',
]

export function colorFor(index) {
  return PALETTE[index % PALETTE.length]
}
