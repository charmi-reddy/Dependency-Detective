// 01 — Everything a component directly relies on (plus its direct dependents).
// Param: $id (component id)

MATCH (n:Component {id: $id})-[r]->(m:Component)
RETURN type(r) AS rel,
       m{.*} AS component,
       [l IN labels(m) WHERE l <> 'Component'][0] AS type
ORDER BY rel, component.name;

// Direct dependents (who directly relies on this component):
MATCH (m:Component)-[r]->(n:Component {id: $id})
RETURN type(r) AS rel,
       m{.*} AS component,
       [l IN labels(m) WHERE l <> 'Component'][0] AS type
ORDER BY component.name;
