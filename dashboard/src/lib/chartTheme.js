export function axisColors(isDark) {
  return {
    grid: isDark ? 'rgba(51,65,85,0.4)' : 'rgba(203,213,225,0.6)',
    tick: isDark ? '#94a3b8' : '#475569',
  }
}

export function tooltipStyle(isDark) {
  return {
    backgroundColor: isDark ? '#0f172a' : '#ffffff',
    border: `1px solid ${isDark ? 'rgba(51,65,85,0.8)' : 'rgba(203,213,225,0.9)'}`,
    borderRadius: '8px',
    fontSize: '12px',
    color: isDark ? '#e2e8f0' : '#1e293b',
  }
}
