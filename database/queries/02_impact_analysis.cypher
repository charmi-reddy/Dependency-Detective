// 02 — Multi-hop impact analysis (the assignment's headline query).
//
// "If this component fails or changes, what else could be affected — and how?"
// Variable-length traversal over six typed relationships, 1..6 hops deep,
// returning each affected component's distance and one shortest chain to the
// origin (used to draw the blast-radius tree).
//
// Param: $id (component id, e.g. "db-postgresql")

MATCH (root:Component {id: $id})
MATCH p = (affected:Component)
          -[:DEPENDS_ON|CALLS|READS_FROM|WRITES_TO|USES|DEPLOYED_ON*1..6]->(root)
WITH affected, min(length(p)) AS depth
MATCH sp = (affected)
           -[:DEPENDS_ON|CALLS|READS_FROM|WRITES_TO|USES|DEPLOYED_ON*1..6]->(root)
WHERE length(sp) = depth
WITH affected, depth, collect(sp)[0] AS chain
RETURN affected{.*} AS component,
       [l IN labels(affected) WHERE l <> 'Component'][0] AS type,
       depth,
       [n IN nodes(chain) | {id: n.id, name: n.name,
                             type: [l IN labels(n) WHERE l <> 'Component'][0]}] AS chain_nodes,
       [r IN relationships(chain) | type(r)] AS chain_rels
ORDER BY depth, component.name;

// Why this is awkward in SQL: the hop count varies per component, the chain
// crosses six relationship kinds and five node types, and you would need a
// recursive CTE plus one JOIN per relationship table per hop. In the graph,
// the dependency network *is* the schema, so the question is one pattern.
