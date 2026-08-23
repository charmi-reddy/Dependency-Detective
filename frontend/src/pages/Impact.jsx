import React from 'react'
import { api, useFetch } from '../api.js'
import { href } from '../router.js'
import ImpactTree from '../components/ImpactTree.jsx'
import {
  BackLink, ComponentRow, CritBadge, Dot, EmptyState, ErrorState, Panel,
  Spinner, StatusPill, TypeBadge,
} from '../components/ui.jsx'

function SummaryStrip({ impact, criticality }) {
  const cells = [
    ['Components affected', impact.total, 'text-rose-300'],
    ['Direct dependents', impact.direct.length, 'text-slate-100'],
    ['Indirect dependents', impact.indirect.length, 'text-slate-100'],
    ['Deepest chain', `${impact.max_depth} hops`, 'text-slate-100'],
  ]
  return (
    <div className="grid grid-cols-2 gap-3 lg:grid-cols-5">
      {cells.map(([label, value, cls]) => (
        <div key={label} className="rounded-xl border border-slate-800 bg-slate-900/60 px-4 py-3">
          <div className="text-[11px] uppercase tracking-wider text-slate-500">{label}</div>
          <div className={`mt-1 text-xl font-semibold ${cls}`}>{value}</div>
        </div>
      ))}
      <div className="col-span-2 rounded-xl border border-slate-800 bg-slate-900/60 px-4 py-3 lg:col-span-1">
        <div className="flex items-center justify-between">
          <span className="text-[11px] uppercase tracking-wider text-slate-500">Criticality</span>
          <CritBadge tier={criticality.tier} />
        </div>
        <div className="mt-2.5 h-1.5 overflow-hidden rounded-full bg-slate-800">
          <div
            className={`h-full rounded-full ${criticality.tier === 'HIGH' ? 'bg-rose-400' : criticality.tier === 'MEDIUM' ? 'bg-amber-400' : 'bg-slate-500'}`}
            style={{ width: `${Math.max(2, criticality.share * 100)}%` }}
          />
        </div>
      </div>
    </div>
  )
}

function DepthBadge({ depth }) {
  return (
    <span className="rounded bg-slate-800 px-1.5 py-0.5 font-mono text-[10px] text-slate-400" title={`${depth} dependency hop${depth === 1 ? '' : 's'} from the origin`}>
      {depth} hop{depth === 1 ? '' : 's'}
    </span>
  )
}

export default function ImpactPage({ id }) {
  const { data, loading, error, refetch } = useFetch(
    () => Promise.all([api.impact(id), api.criticality(id)]).then(([impact, criticality]) => ({ impact, criticality })),
    [id],
  )

  if (loading) {
    return (
      <div>
        <BackLink to={href.component(id)} label="Back to component" />
        <Spinner label="Analyzing dependency graph…" />
      </div>
    )
  }
  if (error) {
    return (
      <div>
        <BackLink to={href.component(id)} label="Back to component" />
        {error.code === 'not_found'
          ? <EmptyState icon="⌕" title="Component not found" message={`“${id}” does not exist in the dependency graph.`} />
          : <ErrorState error={error} onRetry={refetch} />}
      </div>
    )
  }

  const { impact, criticality } = data
  const c = impact.root.component
  const all = [...impact.direct, ...impact.indirect]

  return (
    <div>
      <BackLink to={href.component(id)} label="Back to component" />

      <header className="mb-5">
        <div className="flex flex-wrap items-center gap-3">
          <h1 className="text-2xl font-semibold text-slate-50">Impact analysis</h1>
          <TypeBadge type={impact.root.type} />
          <StatusPill status={c.status} />
        </div>
        <p className="mt-2 max-w-3xl text-sm text-slate-400">
          If <span className="font-medium text-slate-200">{c.name}</span> fails or changes, these are the
          components at risk — found with a multi-hop traversal that walks every dependency chain back to
          the origin, direct and indirect.
        </p>
      </header>

      {impact.total === 0 ? (
        <EmptyState
          icon="◌"
          title={`Nothing depends on ${c.name}`}
          message={`${c.name} is a leaf of the dependency graph — no other component would be affected if it went down.`}
        >
          <a href={href.component(id)} className="mt-5 inline-block rounded-lg border border-slate-600 px-4 py-2 text-sm text-slate-200 transition hover:border-sky-500/60 hover:text-sky-300">
            View its dependencies instead
          </a>
        </EmptyState>
      ) : (
        <div className="space-y-6">
          <SummaryStrip impact={impact} criticality={criticality} />

          <Panel
            title="Blast radius"
            subtitle="Origin on the left; each column is one dependency hop further away. Chains show shortest routes."
          >
            <ImpactTree root={{ name: c.name, type: impact.root.type }} entries={all} />
          </Panel>

          <div className="grid gap-6 lg:grid-cols-2">
            <Panel title={`Direct dependents (${impact.direct.length})`} subtitle="Break immediately — one hop away.">
              <div className="-mx-2">
                {impact.direct.map((e) => (
                  <ComponentRow
                    key={e.component.id}
                    component={e.component}
                    type={e.type}
                    trailing={<span className="font-mono text-[10px] text-slate-500">{e.chain_rels[0]}</span>}
                  />
                ))}
              </div>
            </Panel>
            <Panel title={`Indirect dependents (${impact.indirect.length})`} subtitle="Break through dependency chains — the ones dashboards usually miss.">
              {impact.indirect.length === 0 ? (
                <EmptyState icon="◌" title="No indirect impact" message="Every dependent connects directly." />
              ) : (
                <div className="-mx-2">
                  {impact.indirect.map((e) => (
                    <ComponentRow
                      key={e.component.id}
                      component={e.component}
                      type={e.type}
                      trailing={<DepthBadge depth={e.depth} />}
                    />
                  ))}
                </div>
              )}
            </Panel>
          </div>
        </div>
      )}
    </div>
  )
}
