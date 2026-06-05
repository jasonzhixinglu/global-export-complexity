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

// Bright, full-spectrum categorical palette (blue→orange→green→pink→yellow→teal→
// purple→cyan→lime…), readable on dark. First four = CHN / USA / DEU / JPN.
export const PALETTE = [
  '#3b82f6', '#f97316', '#22c55e', '#ec4899', '#eab308',
  '#14b8a6', '#a855f7', '#ef4444', '#22d3ee', '#84cc16',
  '#8b5cf6', '#fb7185', '#10b981', '#f59e0b', '#d946ef',
  '#0ea5e9', '#f43f5e', '#4ade80', '#facc15', '#2dd4bf',
  '#93c5fd', '#fdba74', '#86efac', '#f9a8d4', '#fde047',
  '#5eead4', '#d8b4fe', '#a5f3fc', '#bef264', '#fda4af',
]

export function colorFor(index) {
  return PALETTE[index % PALETTE.length]
}
