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

// Categorical palette — clean, distinct, readable on dark. First four are the defaults
// (CHN / USA / DEU / JPN): blue / red / green / gold.
export const PALETTE = [
  '#5B8FF9', '#E8684A', '#5AD8A6', '#F6BD16', '#9270CA',
  '#6DC8EC', '#FF9D4D', '#FF99C3', '#269A99', '#5D7092',
  '#3B7DD8', '#E76A3C', '#46B98E', '#E0A800', '#7E5FB0',
  '#56AEDC', '#E08E50', '#D45B9E', '#2E8B8B', '#8694B0',
  '#7E84F7', '#84C262', '#C76F6F', '#73C0DE', '#B58CE0',
  '#4FB3A1', '#F2A0A0', '#9FD356', '#FBC02D', '#A0AEC0',
]

export function colorFor(index) {
  return PALETTE[index % PALETTE.length]
}
