// 04 — Component criticality: graph-derived blast radius.
// Direct and indirect buckets are disjoint (indirect = depth >= 2) so the
// total matches the impact-analysis count exactly.
//
// Param: $id

MATCH (c:Component {id: $id})
OPTIONAL MATCH (d:Component)-[:DEPENDS_ON|CALLS|READS_FROM|WRITES_TO|USES|DEPLOYED_ON]->(c)
WITH count(DISTINCT d) AS direct
OPTIONAL MATCH (x:Component)-[:DEPENDS_ON|CALLS|READS_FROM|WRITES_TO|USES|DEPLOYED_ON*2..6]->(c)
RETURN direct, count(DISTINCT x) AS indirect;
