// 05 — Leaderboard: blast radius of every component, ranked.
// A whole-graph aggregate over a variable-length traversal — expensive and
// clunky to express in relational SQL; a single pattern here.
//
// Param: $limit

MATCH (c:Component)
OPTIONAL MATCH (x:Component)-[:DEPENDS_ON|CALLS|READS_FROM|WRITES_TO|USES|DEPLOYED_ON*1..6]->(c)
WITH c, count(DISTINCT x) AS reach
RETURN c{.*} AS component,
       [l IN labels(c) WHERE l <> 'Component'][0] AS type,
       reach
ORDER BY reach DESC, component.name
LIMIT $limit;
