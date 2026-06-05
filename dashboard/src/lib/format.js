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

// Curated categorical palette — modern, harmonious, distinct in light & dark.
// First four are tuned to look good together (default CHN / USA / DEU / JPN).
export const PALETTE = [
  '#6366f1', '#f59e0b', '#10b981', '#f43f5e', '#38bdf8',
  '#a78bfa', '#2dd4bf', '#fb923c', '#f472b6', '#a3e635',
  '#22d3ee', '#e879f9', '#60a5fa', '#34d399', '#fbbf24',
  '#fb7185', '#818cf8', '#4ade80', '#facc15', '#c084fc',
  '#5eead4', '#fdba74', '#93c5fd', '#d8b4fe', '#86efac',
  '#fcd34d', '#fda4af', '#67e8f9', '#bef264', '#f0abfc',
]

export function colorFor(index) {
  return PALETTE[index % PALETTE.length]
}
