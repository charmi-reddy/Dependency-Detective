import React from 'react'
import { api, useFetch } from '../api.js'
import { href } from '../router.js'
import {
  BackLink, ComponentRow, CritBadge, EmptyState, ErrorState, Panel, RelBadge,
  Spinner, StatusPill, TypeBadge,
} from '../components/ui.jsx'

function NotFound({ id }) {
  return (
    <div>
      <BackLink to={href.dashboard()} label="Back to dashboard" />
      <EmptyState
        icon="⌕"
        title="Component not found"
        message={`“${id}” does not exist in the dependency graph. It may have been renamed or never seeded.`}
      >
        <a
          href={href.dashboard()}
          className="mt-5 inline-block rounded-lg bg-sky-500 px-4 py-2 text-sm font-medium text-slate-950 transition hover:bg-sky-400"
        >
          Search components
        </a>
      </EmptyState>
    </div>
  )
}

function CriticalityCard({ id }) {
  const { data, loading, error, refetch } = useFetch(() => api.criticality(id), [id])
  if (loading) return <Spinner label="Scoring criticality…" />
  if (error) return <ErrorState error={error} onRetry={refetch} />
  if (!data) return null
  return (
    <div>
      <div className="flex items-center justify-between">
        <CritBadge tier={data.tier} />
        <span className="text-xs text-slate-500">
          {(data.share * 100).toFixed(1)}% of the graph
        </span>
      </div>
      <div className="mt-3 h-2 overflow-hidden rounded-full bg-slate-800">
        <div
          className={`h-full rounded-full ${data.tier === 'HIGH' ? 'bg-rose-400' : data.tier === 'MEDIUM' ? 'bg-amber-400' : 'bg-slate-500'}`}
          style={{ width: `${Math.max(2, data.share * 100)}%` }}
        />
      </div>
      <dl className="mt-4 grid grid-cols-3 gap-2 text-center">
        {[
          ['Direct', data.direct],
          ['Indirect', data.indirect],
          ['Total', data.total],
        ].map(([label, value]) => (
          <div key={label} className="rounded-lg border border-slate-800 bg-slate-950/50 px-2 py-2.5">
            <dt className="text-[10px] uppercase tracking-wider text-slate-500">{label}</dt>
            <dd className="mt-0.5 text-lg font-semibold text-slate-100">{value}</dd>
          </div>
        ))}
      </dl>
      <p className="mt-3 text-xs leading-relaxed text-slate-500">
        Components depending on this one, directly ({data.direct}) or through
        intermediate hops ({data.indirect}) — derived entirely from graph traversal.
      </p>
    </div>
  )
}

function DependencyList({ title, rows, emptyTitle, emptyMessage }) {
  // A component can connect through several edge types (e.g. READS_FROM and
  // WRITES_TO the same database) — collapse to one row with one badge per edge.
  const grouped = Object.values(rows.reduce((acc, row) => {
    const g = acc[row.component.id] || (acc[row.component.id] = {
      component: row.component, type: row.type, rels: [],
    })
    g.rels.push(row.rel)
    return acc
  }, {}))

  return (
    <Panel title={title} subtitle={`${grouped.length} component${grouped.length === 1 ? '' : 's'}`}>
      {grouped.length === 0 ? (
        <EmptyState icon="○" title={emptyTitle} message={emptyMessage} />
      ) : (
        <div className="-mx-2">
          {grouped.map((g) => (
            <ComponentRow
              key={g.component.id}
              component={g.component}
              type={g.type}
              trailing={
                <>
                  {g.rels.map((rel) => <RelBadge key={rel} rel={rel} />)}
                  <span className="text-slate-600">›</span>
                </>
              }
            />
          ))}
        </div>
      )}
    </Panel>
  )
}

export default function ComponentPage({ id }) {
  const { data, loading, error, refetch } = useFetch(() => api.dependencies(id), [id])

  if (loading) {
    return (
      <div>
        <BackLink to={href.dashboard()} label="Back to dashboard" />
        <Spinner label="Loading component…" />
      </div>
    )
  }
  if (error) {
    return error.code === 'not_found'
      ? <NotFound id={id} />
      : (
        <div>
          <BackLink to={href.dashboard()} label="Back to dashboard" />
          <ErrorState error={error} onRetry={refetch} />
        </div>
      )
  }

  const { component: record, dependencies, dependents } = data
  const c = record.component
  const detail = [c.database_type && `Type: ${c.database_type}`, c.provider && `Provider: ${c.provider}`,
    c.version && `v${c.version}`, c.language, c.environment && `env: ${c.environment}`]
    .filter(Boolean)

  return (
    <div>
      <BackLink to={href.dashboard()} label="Back to dashboard" />

      <header className="rounded-xl border border-slate-800 bg-slate-900/60 p-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-3">
              <h1 className="text-2xl font-semibold text-slate-50">{c.name}</h1>
              <TypeBadge type={record.type} />
              <StatusPill status={c.status} />
            </div>
            {c.description && <p className="mt-2 max-w-2xl text-sm text-slate-400">{c.description}</p>}
            <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1 font-mono text-xs text-slate-500">
              {detail.map((d) => <span key={d}>{d}</span>)}
              {record.owner && <span>owner: {record.owner}</span>}
              <span>id: {c.id}</span>
            </div>
          </div>
          <div className="flex flex-col gap-2 sm:flex-row">
            <a
              href={href.impact(id)}
              className="rounded-lg bg-rose-500 px-4 py-2 text-center text-sm font-semibold text-white transition hover:bg-rose-400"
            >
              Analyze impact
            </a>
            <a
              href={href.path(id, '')}
              className="rounded-lg border border-slate-600 px-4 py-2 text-center text-sm font-medium text-slate-200 transition hover:border-sky-500/60 hover:text-sky-300"
            >
              Find dependency path
            </a>
          </div>
        </div>
      </header>

      <div className="mt-6 grid gap-6 xl:grid-cols-[1fr_1fr_320px]">
        <DependencyList
          title={`${c.name} relies on`}
          rows={dependencies}
          emptyTitle="No dependencies"
          message={`${c.name} does not rely on any other component — it is a foundation of the graph.`}
        />
        <DependencyList
          title={`Relies on ${c.name}`}
          rows={dependents}
          emptyTitle="No dependents"
          message={`Nothing depends on ${c.name} yet — it is a leaf in the graph.`}
        />
        <Panel title="Criticality">
          <CriticalityCard id={id} />
        </Panel>
      </div>
    </div>
  )
}
