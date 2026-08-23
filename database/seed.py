#!/usr/bin/env python3
"""
Seed CognoDB with the Dependency Detective demo graph.

Usage:
    export COGNODB_URI=bolt+s://<your-instance>.cognodb.com:7687
    export COGNODB_USERNAME=cognodb
    export COGNODB_PASSWORD=<your-password>

    python database/seed.py            # wipes the instance first (asks to confirm)
    python database/seed.py --yes      # non-interactive wipe + seed
    python database/seed.py --dry-run  # print the dataset summary, touch nothing

Everything is written with parameterised Cypher (UNWIND batches + MERGE), so
re-running the script is idempotent after the initial wipe.
"""

from __future__ import annotations

import argparse
import os
import sys
from collections import defaultdict

from dotenv import load_dotenv
from neo4j import GraphDatabase

# Allow running as ``python database/seed.py`` from the repo root.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import seed_data  # noqa: E402
from backend.app.services import cypher  # noqa: E402

LABEL_GROUPS = ["Service", "Database", "API", "Library", "Infrastructure"]

WIPE = "MATCH (n) DETACH DELETE n"

CREATE_CONSTRAINT = """
CREATE CONSTRAINT component_id_unique IF NOT EXISTS
FOR (n:Component) REQUIRE n.id IS UNIQUE
"""

# Labels cannot be Cypher parameters, so nodes are inserted in one query per
# label group (labels come from our own seed data, never user input).
MERGE_NODES = """
UNWIND $rows AS row
MERGE (n:Component:{label} {{id: row.id}})
SET n += row.props
"""

MERGE_TEAM = """
UNWIND $rows AS row
MERGE (t:Team {id: row.id})
SET t += row.props
"""

MERGE_REL = """
UNWIND $rows AS row
MATCH (a {id: row.src}), (b {id: row.dst})
MERGE (a)-[:{rtype}]->(b)
"""


def node_rows_by_label() -> dict[str, list[dict]]:
    groups: dict[str, list[dict]] = defaultdict(list)
    for node_id, label in seed_data.LABELS.items():
        groups[label].append({"id": node_id, "props": seed_data.ALL_PROPERTIES[node_id]})
    return groups


def seed(session) -> None:
    # Uniqueness constraint (best effort: older Bolt servers may reject DDL).
    try:
        session.run(CREATE_CONSTRAINT)
        print("  ✓ uniqueness constraint on Component.id ensured")
    except Exception as exc:  # noqa: BLE001 - constraint support is optional
        print(f"  ! constraint skipped ({exc.__class__.__name__}); continuing")

    groups = node_rows_by_label()
    for label in LABEL_GROUPS:
        session.run(MERGE_NODES.format(label=label), rows=groups[label])
        print(f"  ✓ {len(groups[label]):>2} {label} nodes")
    session.run(MERGE_TEAM, rows=groups["Team"])
    print(f"  ✓ {len(groups['Team']):>2} Team nodes")

    rels_by_type: dict[str, list[dict]] = defaultdict(list)
    for src, rtype, dst in seed_data.RELATIONSHIPS:
        rels_by_type[rtype].append({"src": src, "dst": dst})
    for rtype, rows in sorted(rels_by_type.items()):
        session.run(MERGE_REL.format(rtype=rtype), rows=rows)
        print(f"  ✓ {len(rows):>2} :{rtype} relationships")


def verify(session) -> bool:
    ok = True
    node_counts = {r["type"]: r["count"] for r in session.run(cypher.NODE_COUNT_BY_TYPE).data()}
    total_nodes = sum(node_counts.values())
    rel_counts = {r["type"]: r["count"] for r in session.run(cypher.REL_COUNT_BY_TYPE).data()}
    total_rels = sum(rel_counts.values())
    expected_nodes = seed_data.NODE_COUNT - len(seed_data.TEAMS)  # Component-labelled nodes
    print(f"\n  components: {total_nodes} (expected {expected_nodes})")
    print(f"  relationships: {total_rels} (expected {seed_data.REL_COUNT})")
    if total_nodes != expected_nodes or total_rels != seed_data.REL_COUNT:
        ok = False

    # Smoke-test the headline traversal against the freshly-seeded graph.
    impact = session.run(cypher.IMPACT_ANALYSIS, id="db-postgresql").data()
    names = ", ".join(r["component"]["name"] for r in impact[:6])
    print(f"\n  smoke test — impact of PostgreSQL outage: {len(impact)} components affected")
    print(f"  e.g. {names}, …")
    if len(impact) < 10:
        ok = False
    return ok


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--yes", action="store_true", help="skip wipe confirmation")
    parser.add_argument("--dry-run", action="store_true", help="print summary and exit")
    args = parser.parse_args()

    print("Dependency Detective — CognoDB seed\n")
    print(f"  dataset: {seed_data.NODE_COUNT} nodes, {seed_data.REL_COUNT} relationships")
    if args.dry_run:
        for label, rows in sorted(node_rows_by_label().items()):
            print(f"    {label:<15} {len(rows)}")
        return 0

    load_dotenv()
    uri = os.getenv("COGNODB_URI", "")
    user = os.getenv("COGNODB_USERNAME", "cognodb")
    password = os.getenv("COGNODB_PASSWORD", "")
    if not uri or not password:
        print("ERROR: set COGNODB_URI and COGNODB_PASSWORD (see .env.example).", file=sys.stderr)
        return 2

    if not args.yes:
        answer = input(f"\nThis will DELETE ALL DATA on {uri} and reseed. Continue? [y/N] ")
        if answer.strip().lower() != "y":
            print("Aborted.")
            return 1

    driver = GraphDatabase.driver(uri, auth=(user, password))
    try:
        driver.verify_connectivity()
        with driver.session() as session:
            print("\nWiping existing data…")
            session.run(WIPE)
            print("Seeding…")
            seed(session)
            print("\nVerifying…")
            ok = verify(session)
    finally:
        driver.close()

    print("\n" + ("Seed complete ✔" if ok else "Seed finished WITH WARNINGS — check counts above."))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
