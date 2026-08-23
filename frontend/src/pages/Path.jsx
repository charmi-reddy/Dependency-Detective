import React, { useMemo, useState } from 'react'
import { api, useFetch } from '../api.js'
import { href, navigate } from '../router.js'
import {
  Dot, EmptyState, ErrorState, Panel, RelBadge, Spinner, TypeBadge, REL_VERBS,
} from '../components/ui.jsx'

function NodeCard({ node, last }) {
  return (
    <a
      href={href.component(node.id)}
      className="flex items-center gap-3 rounded-xl border border-slate-700 bg-slate-900 px-4 py-3 transition hover:border-sky-500/60"
    >
      <Dot type={node.type} />
      <span className="text-sm font-medium text-slate-100">{node.name}</span>
      <span className="ml-auto"><TypeBadge type={node.type} /></span>
    </a>
  )
}

function Connector({ rel }) {
  return (
    <div className="flex flex-col items-center gap-1 py-1" aria-hidden>
      <div className="h-4 w-px bg-slate-600" />
      <span className="rounded-full border border-slate-700 bg-slate-900 px-2.5 py-1 text-[10px] text-slate-400">
        <span className="font-mono">{rel}</span>
        <span className="ml-1.5 text-slate-500">{REL_VERBS[rel] || ''}</span>
      </span>
      <div className="h-4 w-px bg-slate-600" />
      <svg viewBox="0 0 12 12" className="h-3 w-3 text-slate-500" fill="currentColor">
        <path d="M6 12 1 5h10L6 12Z" />
      </svg>
    </div>
  )
}

function ChainView({ path }) {
  const items = []
  path.nodes.forEach((node, i) => {
    items.push(<NodeCard key={`n-${i}`} node={node} />)
    if (i < path.rels.length) {
      items.push(<Connector key={`r-${i}`} rel={path.rels[i]} />)
    }
  })
  return <div className="mx-auto max-w-xl">{items}</div>
}

function Selector({ label, value, onChange, options, exclude }) {
  return (
    <label className="block min-w-0 flex-1">
      <span className="mb-1.5 block text-[11px] font-medium uppercase tracking-wider text-slate-500">{label}</span>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full truncate rounded-lg border border-slate-700 bg-slate-900 px-3 py-2.5 text-sm text-slate-100 focus:border-sky-500/70 focus:outline-none"
      >
        <option value="">Select a component…</option>
        {options.filter((o) => o.id !== exclude).map((o) => (
          <option key={o.id} value={o.id}>
            {o.name} — {o.type}
          </option>
        ))}
      </select>
    </label>
  )
}

export default function PathPage({ from, to }) {
  const [promoted, setPromoted] = useState(null)
  const list = useFetch(() => api.search('', { limit: 100 }), [])
  const options = useMemo(
    () => (list.data || []).map((row) => ({ id: row.component.id, name: row.component.name, type: row.type })),
    [list.data],
  )

  const ready = Boolean(from && to && from !== to)
  const result = useFetch(
    () => (ready ? api.path(from, to) : Promise.resolve(null)),
    [from, to],
  )

  const update = (newFrom, newTo) => {
    setPromoted(null)
    navigate(href.path(newFrom, newTo))
  }

  const nameOf = (id) => options.find((o) => o.id === id)?.name || id
  const primary = promoted ?? result.data?.paths?.[0]

  return (
    <div className="space-y-6">
      <div className="pt-2">
        <h1 className="text-xl font-semibold text-slate-50">Dependency path finder</h1>
        <p className="mt-1 text-sm text-slate-400">
          “Why does A depend on B?” — trace the exact chain of relationships connecting two components.
        </p>
      </div>

      <Panel>
        <div className="flex flex-col items-stretch gap-3 sm:flex-row sm:items-end">
          <Selector label="From" value={from} onChange={(v) => update(v, to)} options={options} exclude={to} />
          <button
            onClick={() => update(to, from)}
            disabled={!from && !to}
            title="Swap direction"
            className="mx-auto rounded-lg border border-slate-700 p-2.5 text-slate-400 transition hover:border-sky-500/60 hover:text-sky-300 disabled:opacity-40"
          >
            <svg viewBox="0 0 20 20" className="h-4 w-4" fill="currentColor">
              <path d="M13.7 2.3a1 1 0 0 0-1.4 1.4L14.6 6H4a1 1 0 1 0 0 2h10.6l-2.3 2.3a1 1 0 1 0 1.4 1.4l4-4a1 1 0 0 0 0-1.4l-4-4ZM6.3 17.7a1 1 0 0 0 1.4-1.4L5.4 14H16a1 1 0 1 0 0-2H5.4l2.3-2.3a1 1 0 0 0-1.4-1.4l-4 4a1 1 0 0 0 0 1.4l4 4Z" />
            </svg>
          </button>
          <Selector label="To" value={to} onChange={(v) => update(from, v)} options={options} exclude={from} />
          <span
            className="text-center text-xs text-slate-500 sm:pb-3"
            title="All matching paths are traversed, shortest first"
          >
            shortest first
          </span>
        </div>
      </Panel>

      {!ready && (
        <EmptyState
          icon="⇄"
          title="Pick two components"
          message="Choose a source and a target above to trace how they are connected through the dependency graph."
        />
      )}

      {ready && result.loading && <Spinner label="Tracing dependency paths…" />}

      {ready && result.error && (
        <ErrorState error={result.error} onRetry={result.refetch} />
      )}

      {ready && result.data && !result.data.found && (
        <EmptyState
          icon="⊘"
          title="No dependency path found"
          message={`There is no directed dependency chain from “${nameOf(from)}” to “${nameOf(to)}”. Dependencies may flow in the opposite direction, or the components may live in isolated parts of the graph.`}
        >
          <button
            onClick={() => update(to, from)}
            className="mt-5 rounded-lg border border-slate-600 px-4 py-2 text-sm text-slate-200 transition hover:border-sky-500/60 hover:text-sky-300"
          >
            Try the reverse direction
          </button>
        </EmptyState>
      )}

      {ready && result.data?.found && primary && (
        <div className="space-y-6">
          <Panel
            title={`How ${nameOf(from)} depends on ${nameOf(to)}`}
            subtitle={`Connected in ${primary.hops} hop${primary.hops === 1 ? '' : 's'}${result.data.paths.length > 1 ? ` — ${result.data.paths.length - 1} alternative route${result.data.paths.length - 1 === 1 ? '' : 's'} below` : ''}.`}
          >
            <ChainView path={primary} />
          </Panel>

          {result.data.paths.length > 1 && (
            <Panel title="Alternative routes" subtitle="Click one to inspect it. Same destination, different chain of custody.">
              <ul className="space-y-2">
                {result.data.paths.map((p, i) => i === (promoted ? result.data.paths.indexOf(promoted) : 0) ? null : (
                  <li key={i}>
                    <button
                      onClick={() => { setPromoted(p); window.scrollTo({ top: 0, behavior: 'smooth' }) }}
                      className="flex w-full items-center justify-between gap-3 rounded-lg border border-slate-800 bg-slate-950/40 px-4 py-2.5 text-left transition hover:border-sky-500/50"
                    >
                      <span className="truncate font-mono text-xs text-slate-400">
                        {p.nodes.map((n) => n.name).join(' → ')}
                      </span>
                      <span className="shrink-0 rounded bg-slate-800 px-1.5 py-0.5 font-mono text-[10px] text-slate-400">
                        {p.hops} hops
                      </span>
                    </button>
                  </li>
                ))}
              </ul>
            </Panel>
          )}
        </div>
      )}
    </div>
  )
}
