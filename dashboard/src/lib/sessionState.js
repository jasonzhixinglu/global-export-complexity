import { useState, useCallback } from 'react'

// useState mirrored into sessionStorage; survives tab switches within the browser tab.
export function useSessionState(key, defaultValue) {
  const [value, setValue] = useState(() => {
    try {
      const v = sessionStorage.getItem(key)
      return v == null ? defaultValue : JSON.parse(v)
    } catch {
      return defaultValue
    }
  })
  const setAndPersist = useCallback((v) => {
    setValue(prev => {
      const next = typeof v === 'function' ? v(prev) : v
      try { sessionStorage.setItem(key, JSON.stringify(next)) } catch {}
      return next
    })
  }, [key])
  return [value, setAndPersist]
}
