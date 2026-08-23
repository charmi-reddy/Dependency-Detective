import React from 'react'
import { TYPE_META } from './ui.jsx'

/**
 * Blast-radius tree.
 *
 * The backend returns one shortest chain per affected component
 * (affected → … → root). We stitch those chains into a tree rooted at the
 * failing component: parents = next hop towards the root, columns = hop depth.
 * Leaves are stacked top-down, parents sit at the mean of their children —
 * ~30 lines of layout instead of pulling in a full graph-visualisation lib.
 */

const COL_W = 235
const ROW_H = 46
const PAD = 16
const NODE_W = 196
const NODE_H = 34

export default function ImpactTree({ root, entries }) {
  if (!entries?.length) return null

  const byId = {}
  const children = { root: [] }
  let maxDepth = 0

  for (const e of entries) {
    byId[e.component.id] = e
    maxDepth = Math.max(maxDepth, e.depth)
    const parentId = e.depth === 1 ? 'root' : e.chain_nodes?.[1]?.id || 'root'
    ;(children[parentId] = children[parentId] || []).push(e.component.id)
  }
  Object.values(children).forEach((list) => list.sort((a, b) => byId[a].component.name.localeCompare(byId[b].component.name)))

  // Leaf-first y placement
  let leafSlot = 0
  const rowOf = {}
  const place = (id) => {
    const kids = (children[id] || []).filter((k) => byId[k])
    if (!kids.length) {
      rowOf[id] = leafSlot++
      return rowOf[id]
    }
    const rows = kids.map(place)
    rowOf[id] = (Math.min(...rows) + Math.max(...rows)) / 2
    return rowOf[id]
  }
  place('root')

  const depthOf = (id) => (id === 'root' ? 0 : byId[id].depth)
  const x = (id) => PAD + depthOf(id) * COL_W
  const y = (id) => PAD + rowOf[id] * ROW_H

  const width = PAD * 2 + (maxDepth + 1) * COL_W
  const height = PAD * 2 + Math.max(leafSlot, 1) * ROW_H

  const nodeName = (id) => (id === 'root' ? root.name : byId[id].component.name)
  const nodeType = (id) => (id === 'root' ? root.type : byId[id].type)

  const allIds = ['root', ...Object.keys(byId)]
  const edges = Object.entries(children).flatMap(([pid, kids]) => kids.map((cid) => [pid, cid]))

  return (
    <div className="overflow-x-auto">
      <svg width={width} height={height} className="select-none" role="img" aria-label="Impact tree">
        {edges.map(([pid, cid]) => {
          const x1 = x(pid) + NODE_W
          const y1 = y(pid) + NODE_H / 2
          const x2 = x(cid)
          const y2 = y(cid) + NODE_H / 2
          const mx = (x1 + x2) / 2
          return (
            <path
              key={`${pid}-${cid}`}
              d={`M ${x1} ${y1} C ${mx} ${y1}, ${mx} ${y2}, ${x2} ${y2}`}
              fill="none"
              stroke="#475569"
              strokeWidth={1.4}
              strokeOpacity={0.75}
            />
          )
        })}
        {allIds.map((id) => {
          const meta = TYPE_META[nodeType(id)] || TYPE_META.Team
          const name = nodeName(id)
          const short = name.length > 25 ? `${name.slice(0, 23)}…` : name
          return (
            <g key={id} transform={`translate(${x(id)}, ${y(id)})`}>
              <rect
                width={NODE_W}
                height={NODE_H}
                rx={8}
                fill={id === 'root' ? '#1e293b' : '#0f172a'}
                stroke={meta.hex}
                strokeWidth={id === 'root' ? 2.2 : 1.2}
                strokeOpacity={id === 'root' ? 1 : 0.8}
              />
              <circle cx={13} cy={NODE_H / 2} r={4} fill={meta.hex} />
              <text x={24} y={NODE_H / 2 + 4} fontSize={11.5} fill="#e2e8f0">
                {short}
                <title>{name}</title>
              </text>
              {id === 'root' && (
                <text x={NODE_W - 8} y={NODE_H / 2 + 3.5} fontSize={9.5} fill="#94a3b8" textAnchor="end" fontFamily="ui-monospace, monospace">
                  ORIGIN
                </text>
              )}
            </g>
          )
        })}
      </svg>
    </div>
  )
}
