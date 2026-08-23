import { useCallback, useEffect, useRef, useState } from 'react'

/**
 * Tiny REST client. The browser only ever talks to our Flask backend —
 * CognoDB credentials never leave the server. VITE_API_BASE stays empty when
 * the frontend and backend are served from one origin (or via the Vite dev
 * proxy); set it only for split frontend/backend hosting.
 */

const API_BASE = import.meta.env.VITE_API_BASE || ''

async function request(path) {
  let res
  try {
    res = await fetch(`${API_BASE}/api${path}`)
  } catch {
    throw { status: 0, code: 'network_error', message: 'Unable to reach the server.' }
  }
  let body = null
  try {
    body = await res.json()
  } catch {
    /* non-JSON body */
  }
  if (!res.ok) {
    throw {
      status: res.status,
      code: body?.error?.code || 'error',
      message: body?.error?.message || `Request failed (${res.status}).`,
    }
  }
  return body
}

const qs = (params) => {
  const p = new URLSearchParams()
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== '') p.set(k, v)
  })
  const s = p.toString()
  return s ? `?${s}` : ''
}

export const api = {
  health: () => request('/health'),
  stats: () => request('/stats'),
  search: (q, opts = {}) => request(`/components${qs({ q, type: opts.type, limit: opts.limit })}`),
  component: (id) => request(`/components/${id}`),
  dependencies: (id) => request(`/components/${id}/dependencies`),
  impact: (id) => request(`/components/${id}/impact`),
  criticality: (id) => request(`/components/${id}/criticality`),
  leaderboard: (limit = 8) => request(`/criticality${qs({ limit })}`),
  path: (from, to) => request(`/path${qs({ from, to })}`),
}

/**
 * Data-fetching hook driving the three UI states the assignment asks for:
 * loading / error (with retry) / empty-or-data.
 */
export function useFetch(fn, deps = []) {
  const [state, setState] = useState({ data: null, loading: true, error: null })
  const fnRef = useRef(fn)
  fnRef.current = fn

  const run = useCallback(() => {
    let cancelled = false
    setState({ data: null, loading: true, error: null })
    fnRef.current()
      .then((data) => !cancelled && setState({ data, loading: false, error: null }))
      .catch((error) => !cancelled && setState({ data: null, loading: false, error }))
    return () => {
      cancelled = true
    }
  }, deps) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(run, [run])
  return { ...state, refetch: run }
}

export function useDebounced(value, delay = 200) {
  const [v, setV] = useState(value)
  useEffect(() => {
    const t = setTimeout(() => setV(value), delay)
    return () => clearTimeout(t)
  }, [value, delay])
  return v
}
