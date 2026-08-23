#!/usr/bin/env python3
"""Generate docs/graph-model.svg — the graph data-model diagram for the README.

Run:  python scripts/make_diagram.py
Positions were laid out by hand; edge endpoints are computed against the node
bounding boxes so lines never overlap node interiors.
"""

from pathlib import Path

W, H = 1160, 672
NW, NH = 170, 40  # node box size
COLORS = {
    "Service": "#38bdf8",
    "Database": "#34d399",
    "API": "#fbbf24",
    "Library": "#a78bfa",
    "Infrastructure": "#fb7185",
    "Team": "#94a3b8",
}

# id -> (label, type, cx, cy, sub)
NODES = [
    ("portal", "Customer Portal", "Service", 170, 90, "id · name · team · env · status"),
    ("checkout", "Checkout Service", "Service", 420, 90, ""),
    ("payment", "Payment Service", "Service", 670, 90, ""),
    ("auth", "Auth Service", "Service", 920, 90, ""),
    ("notif", "Notification Service", "Service", 170, 210, ""),
    ("stripe", "Stripe API", "API", 670, 210, "id · name · provider · status"),
    ("pg", "PostgreSQL", "Database", 920, 210, "id · name · database_type · env · status"),
    ("sendgrid", "SendGrid API", "API", 170, 330, ""),
    ("order", "Order Service", "Service", 420, 330, ""),
    ("pyjwt", "PyJWT", "Library", 670, 330, "id · name · version · language"),
    ("analytics", "Analytics Service", "Service", 920, 330, ""),
    ("k8s", "Kubernetes Cluster", "Infrastructure", 420, 510, "id · name · provider · env"),
    ("team", "Identity Team", "Team", 1050, 62, ""),
]

# (from, to, rel, label_dx, label_dy)
EDGES = [
    ("portal", "checkout", "DEPENDS_ON", 0, -12),
    ("checkout", "payment", "DEPENDS_ON", 0, -12),
    ("payment", "auth", "DEPENDS_ON", 0, -12),
    ("payment", "stripe", "CALLS", 10, 0),
    ("auth", "pg", "READS_FROM", 10, 0),
    ("portal", "notif", "DEPENDS_ON", 10, 0),
    ("notif", "sendgrid", "CALLS", 10, 0),
    ("order", "pg", "WRITES_TO", -30, -16),
    ("auth", "pyjwt", "USES", 26, -14),
    ("analytics", "pg", "READS_FROM", 10, 0),
    ("notif", "k8s", "DEPLOYED_ON", -6, 4),
    ("auth", "team", "OWNED_BY", 0, -12),
]

node = {nid: (label, typ, cx, cy, sub) for nid, label, typ, cx, cy, sub in NODES}


def border_point(cx, cy, tx, ty):
    """Point where segment (cx,cy)->(tx,ty) exits the box centred at (cx,cy)."""
    dx, dy = tx - cx, ty - cy
    ts = []
    if dx:
        ts.append((NW / 2) / abs(dx))
    if dy:
        ts.append((NH / 2) / abs(dy))
    t = min(ts) if ts else 0
    return cx + dx * t, cy + dy * t


parts = []
parts.append(
    f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
    f'font-family="ui-sans-serif, system-ui, sans-serif">'
)
parts.append(f'<rect width="{W}" height="{H}" rx="14" fill="#020617"/>')
parts.append(
    '<text x="32" y="34" font-size="16" font-weight="600" fill="#f1f5f9">'
    'Dependency Detective — graph data model</text>'
)

# --- edges ---
for src, dst, rel, ldx, ldy in EDGES:
    _, _, x1, y1, _ = node[src]
    _, _, x2, y2, _ = node[dst]
    sx, sy = border_point(x1, y1, x2, y2)
    ex, ey = border_point(x2, y2, x1, y1)
    ang_dx, ang_dy = sx - ex, sy - ey
    length = (ang_dx**2 + ang_dy**2) ** 0.5 or 1
    ux, uy = ang_dx / length, ang_dy / length
    ax, ay = ex, ey  # arrow tip
    a1x, a1y = ax + ux * 9 - uy * 4.5, ay + uy * 9 + ux * 4.5
    a2x, a2y = ax + ux * 9 + uy * 4.5, ay + uy * 9 - ux * 4.5
    parts.append(
        f'<line x1="{sx:.1f}" y1="{sy:.1f}" x2="{ex:.1f}" y2="{ey:.1f}" '
        f'stroke="#475569" stroke-width="1.5"/>'
    )
    parts.append(
        f'<polygon points="{ax:.1f},{ay:.1f} {a1x:.1f},{a1y:.1f} {a2x:.1f},{a2y:.1f}" '
        f'fill="#475569"/>'
    )
    mx, my = (sx + ex) / 2 + ldx, (sy + ey) / 2 + ldy
    w = len(rel) * 7 + 14
    parts.append(
        f'<rect x="{mx - w/2:.1f}" y="{my - 9}" width="{w}" height="16" rx="4" '
        f'fill="#0f172a" stroke="#334155" stroke-width="1"/>'
    )
    parts.append(
        f'<text x="{mx:.1f}" y="{my + 3}" font-size="10.5" fill="#94a3b8" '
        f'text-anchor="middle" font-family="ui-monospace, monospace">{rel}</text>'
    )

# --- nodes ---
for nid, label, typ, cx, cy, sub in NODES:
    color = COLORS[typ]
    parts.append(
        f'<rect x="{cx - NW/2}" y="{cy - NH/2}" width="{NW}" height="{NH}" rx="9" '
        f'fill="#0f172a" stroke="{color}" stroke-width="1.4"/>'
    )
    parts.append(f'<circle cx="{cx - NW/2 + 16}" cy="{cy}" r="5" fill="{color}"/>')
    parts.append(
        f'<text x="{cx - NW/2 + 28}" y="{cy + 4.5}" font-size="12.5" '
        f'font-weight="600" fill="#e2e8f0">{label}</text>'
    )
    if sub:
        parts.append(
            f'<text x="{cx - NW/2 + 2}" y="{cy + NH/2 + 14}" font-size="9" '
            f'fill="#64748b" font-family="ui-monospace, monospace">{sub}</text>'
        )

# --- legend ---
ly = 566
parts.append(
    f'<rect x="24" y="{ly - 18}" width="{W - 48}" height="88" rx="10" '
    f'fill="#0f172a" stroke="#1e293b" stroke-width="1"/>'
)
parts.append(f'<text x="40" y="{ly + 4}" font-size="11" font-weight="600" fill="#cbd5e1">Node labels</text>')
lx = 150
for typ, color in COLORS.items():
    parts.append(f'<circle cx="{lx}" cy="{ly}" r="5" fill="{color}"/>')
    parts.append(f'<text x="{lx + 10}" y="{ly + 4}" font-size="11" fill="#cbd5e1">{typ}</text>')
    lx += 58 + len(typ) * 6.4
parts.append(
    f'<text x="40" y="{ly + 34}" font-size="11" font-weight="600" fill="#cbd5e1">Rules</text>'
)
parts.append(
    f'<text x="150" y="{ly + 34}" font-size="11" fill="#94a3b8">'
    ':Component base label on every component · edges point from dependent to dependency · '
    ':OWNED_BY excluded from traversals'
    '</text>'
)
parts.append(
    f'<text x="40" y="{ly + 58}" font-size="11" font-weight="600" fill="#cbd5e1">Traversal</text>'
)
parts.append(
    f'<text x="150" y="{ly + 58}" font-size="11" fill="#94a3b8" font-family="ui-monospace, monospace">'
    '(affected)-[:DEPENDS_ON|CALLS|READS_FROM|WRITES_TO|USES|DEPLOYED_ON*1..6]-&gt;(origin)'
    '</text>'
)

parts.append("</svg>")
out = Path(__file__).resolve().parents[1] / "docs" / "graph-model.svg"
out.write_text("\n".join(parts))
print(f"wrote {out}")
