// 03 — "Why does A depend on B?" — all dependency chains, shortest first.
// Answers with the actual relationship path, not just a yes/no.
//
// Params: $fromId, $toId, $maxPaths (e.g. 6)

MATCH (a:Component {id: $fromId}), (b:Component {id: $toId})
MATCH p = (a)-[:DEPENDS_ON|CALLS|READS_FROM|WRITES_TO|USES|DEPLOYED_ON*1..8]->(b)
RETURN [n IN nodes(p) | {id: n.id, name: n.name,
                         type: [l IN labels(n) WHERE l <> 'Component'][0]}] AS nodes,
       [r IN relationships(p) | type(r)] AS rels
ORDER BY length(p) ASC
LIMIT $maxPaths;
