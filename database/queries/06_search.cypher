// 06 — Component search with optional type filter.
// Params: $q (substring, '' = all), $typeLabel ('' = all), $limit

MATCH (n:Component)
WHERE ($q = '' OR toLower(n.name) CONTAINS toLower($q))
  AND ($typeLabel = '' OR $typeLabel IN labels(n))
RETURN n{.*} AS component,
       [l IN labels(n) WHERE l <> 'Component'][0] AS type
ORDER BY n.name
LIMIT $limit;
