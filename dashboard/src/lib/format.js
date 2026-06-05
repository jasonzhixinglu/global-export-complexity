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

// 20-colour categorical palette (distinct in light & dark)
export const PALETTE = [
  '#ef4444', '#3b82f6', '#22c55e', '#a855f7', '#f59e0b',
  '#06b6d4', '#ec4899', '#84cc16', '#f97316', '#8b5cf6',
  '#14b8a6', '#eab308', '#f43f5e', '#0ea5e9', '#10b981',
  '#d946ef', '#fb7185', '#65a30d', '#fbbf24', '#2dd4bf',
  '#60a5fa', '#c084fc', '#4ade80', '#facc15', '#fca5a5',
  '#34d399', '#a78bfa', '#fdba74', '#67e8f9', '#fda4af',
]

export function colorFor(index) {
  return PALETTE[index % PALETTE.length]
}
