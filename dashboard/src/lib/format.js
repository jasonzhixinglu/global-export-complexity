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

// Nice y-axis ceiling for SHARE charts: the smallest "round" share threshold that leaves some
// breathing room above the data peak — a middle ground between always pinning 100% (wastes space
// when the selection is a small share) and hugging the data (stretches the chart). The peak fills
// at most FILL of the axis height, so there's always headroom up top (e.g. a 38% peak → 50%, a 7%
// peak → 10%). Capped at 1.0 so the axis never exceeds 100%.
const SHARE_STEPS = [0.02, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.4, 0.5, 0.6, 0.75, 1]
const FILL = 0.8
export function niceShareMax(max) {
  if (!(max > 0)) return SHARE_STEPS[0]
  for (const s of SHARE_STEPS) if (max <= FILL * s + 1e-9) return s
  return 1
}

// Round, evenly-spaced tick values from 0 to a niceShareMax ceiling, so axis labels land on
// standardized intervals (e.g. ceiling 0.5 → 0/10/20/30/40/50%) instead of recharts' auto
// fractions. The step per ceiling keeps ~3–6 ticks, each a whole-percent value.
const SHARE_TICK_STEP = {
  0.02: 0.01, 0.05: 0.01, 0.1: 0.02, 0.15: 0.05, 0.2: 0.05, 0.25: 0.05,
  0.3: 0.1, 0.4: 0.1, 0.5: 0.1, 0.6: 0.2, 0.75: 0.25, 1: 0.2,
}
export function shareTicks(ceiling) {
  const step = SHARE_TICK_STEP[ceiling] || ceiling / 5
  const n = Math.round(ceiling / step)
  return Array.from({ length: n + 1 }, (_, i) => Math.round(i * step * 1000) / 1000)
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

// Persistent, collision-free colour keyed by a STABLE index, so an entity keeps its colour across
// ranks/years (the Tech views) instead of colour-by-rank (where the #1 series is always blue and a
// rank swap leaves the colours unchanged). The curated bright palette covers the top-30 economies
// (where the tech players sit); golden-angle HSL fills ranks 30+ (rarely co-displayed). 64 slots >
// the ~51 tracked economies, so no two collide.
const DISTINCT = [
  ...PALETTE,
  ...Array.from({ length: 34 }, (_, k) => {
    const h = ((k + 7) * 137.508) % 360            // offset so extras don't echo the early palette
    return `hsl(${h.toFixed(1)}, 55%, ${k % 2 ? 68 : 54}%)`
  }),
]
export function distinctColor(index) {
  const n = DISTINCT.length
  return DISTINCT[(((index | 0) % n) + n) % n]
}
