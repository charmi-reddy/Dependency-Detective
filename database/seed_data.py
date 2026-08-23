"""
Canonical seed dataset for Dependency Detective.

This module is the single source of truth for the demo system graph. It is used by:

  * ``database/seed.py``        - pushes the graph into CognoDB with parameterised Cypher
  * ``backend`` demo backend    - serves the same graph in-memory when no CognoDB
                                  instance is configured (offline development)
  * ``backend/tests``           - asserts on graph structure

Data model
----------
Every entity carries the base label ``Component`` plus exactly one type label:
``Service``, ``Database``, ``API``, ``Library`` or ``Infrastructure``.
Teams are modelled with their own ``Team`` label.

Relationship types (all directions follow the dependency direction):

  (Service)-[:DEPENDS_ON]->(Service | Infrastructure)
  (Service)-[:CALLS]->(API)
  (Service)-[:READS_FROM | WRITES_TO]->(Database)
  (Service)-[:USES]->(Library)
  (Service)-[:DEPLOYED_ON]->(Infrastructure)
  (Service)-[:OWNED_BY]->(Team)

The service-to-service core is intentionally acyclic so impact trees render
cleanly; ``validate()`` enforces that on import.
"""

from __future__ import annotations

# Relationship types that participate in dependency traversal / impact analysis.
# OWNED_BY is deliberately excluded: ownership is organisational metadata, not a
# runtime dependency, so failing components should not "page" teams in the math.
DEPENDENCY_TYPES = [
    "DEPENDS_ON",
    "CALLS",
    "READS_FROM",
    "WRITES_TO",
    "USES",
    "DEPLOYED_ON",
]

# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------
# Each entry: (id, [type label], {properties})

TEAMS = [
    ("team-payments", {"name": "Payments Team", "oncall": "#oncall-payments"}),
    ("team-platform", {"name": "Platform Team", "oncall": "#oncall-platform"}),
    ("team-frontend", {"name": "Frontend Team", "oncall": "#oncall-frontend"}),
    ("team-identity", {"name": "Identity Team", "oncall": "#oncall-identity"}),
    ("team-data", {"name": "Data Team", "oncall": "#oncall-data"}),
    ("team-devops", {"name": "DevOps Team", "oncall": "#oncall-devops"}),
    ("team-notifications", {"name": "Notifications Team", "oncall": "#oncall-notifications"}),
]

SERVICES = [
    ("svc-customer-portal", {
        "name": "Customer Portal", "description": "Public web storefront used by customers to browse and buy.",
        "team": "Frontend Team", "environment": "production", "status": "operational", "language": "TypeScript",
    }),
    ("svc-admin-dashboard", {
        "name": "Admin Dashboard", "description": "Internal console for support and operations staff.",
        "team": "Frontend Team", "environment": "production", "status": "operational", "language": "TypeScript",
    }),
    ("svc-mobile-api-gateway", {
        "name": "Mobile API Gateway", "description": "Backend-for-frontend aggregating APIs for the mobile apps.",
        "team": "DevOps Team", "environment": "production", "status": "operational", "language": "Python",
    }),
    ("svc-checkout", {
        "name": "Checkout Service", "description": "Orchestrates the checkout flow: cart, order, payment, stock.",
        "team": "Payments Team", "environment": "production", "status": "operational", "language": "Python",
    }),
    ("svc-payment", {
        "name": "Payment Service", "description": "Authorises and captures payments via external providers.",
        "team": "Payments Team", "environment": "production", "status": "operational", "language": "Python",
    }),
    ("svc-auth", {
        "name": "Auth Service", "description": "Issues and validates JWT sessions; guards login with reCAPTCHA.",
        "team": "Identity Team", "environment": "production", "status": "operational", "language": "Python",
    }),
    ("svc-notification", {
        "name": "Notification Service", "description": "Sends email, SMS and push notifications from queued events.",
        "team": "Notifications Team", "environment": "production", "status": "operational", "language": "Python",
    }),
    ("svc-user-profile", {
        "name": "User Profile Service", "description": "CRUD for customer profiles, addresses and preferences.",
        "team": "Identity Team", "environment": "production", "status": "operational", "language": "Python",
    }),
    ("svc-cart", {
        "name": "Cart Service", "description": "Session-scoped shopping carts backed by Redis.",
        "team": "Platform Team", "environment": "production", "status": "operational", "language": "Python",
    }),
    ("svc-order", {
        "name": "Order Service", "description": "Persists orders and publishes order lifecycle events.",
        "team": "Platform Team", "environment": "production", "status": "operational", "language": "Python",
    }),
    ("svc-invoice", {
        "name": "Invoice Service", "description": "Generates invoice documents for completed orders.",
        "team": "Payments Team", "environment": "production", "status": "operational", "language": "Python",
    }),
    ("svc-inventory", {
        "name": "Inventory Service", "description": "Tracks stock levels and reservations.",
        "team": "Platform Team", "environment": "production", "status": "maintenance", "language": "Python",
    }),
    ("svc-catalog", {
        "name": "Catalog Service", "description": "Product catalogue, pricing and media references.",
        "team": "Platform Team", "environment": "production", "status": "operational", "language": "JavaScript",
    }),
    ("svc-image", {
        "name": "Image Service", "description": "Resizes and serves product images stored in S3.",
        "team": "Platform Team", "environment": "production", "status": "operational", "language": "Python",
    }),
    ("svc-search", {
        "name": "Search Service", "description": "Product search and autocomplete powered by Elasticsearch.",
        "team": "Platform Team", "environment": "production", "status": "degraded", "language": "Python",
    }),
    ("svc-recommendation", {
        "name": "Recommendation Service", "description": "Personalised product recommendations from behavioural data.",
        "team": "Data Team", "environment": "production", "status": "degraded", "language": "Python",
    }),
    ("svc-analytics", {
        "name": "Analytics Service", "description": "Near-real-time metrics pipeline over warehouse data.",
        "team": "Data Team", "environment": "production", "status": "operational", "language": "Python",
    }),
    ("svc-reporting", {
        "name": "Reporting Service", "description": "Scheduled business reports delivered to Slack.",
        "team": "Data Team", "environment": "production", "status": "operational", "language": "Python",
    }),
    ("svc-fraud-detection", {
        "name": "Fraud Detection Service", "description": "Scores transactions using velocity checks and history.",
        "team": "Payments Team", "environment": "production", "status": "operational", "language": "Python",
    }),
    ("svc-session", {
        "name": "Session Service", "description": "Server-side session storage used by Auth.",
        "team": "Identity Team", "environment": "production", "status": "operational", "language": "Python",
    }),
    ("svc-audit-log", {
        "name": "Audit Log Service", "description": "Immutable append-only audit trail for sensitive actions.",
        "team": "Platform Team", "environment": "production", "status": "operational", "language": "Python",
    }),
    ("svc-shipping", {
        "name": "Shipping Service", "description": "Quotes shipping options and validates delivery addresses.",
        "team": "Platform Team", "environment": "production", "status": "operational", "language": "Python",
    }),
]

DATABASES = [
    ("db-postgresql", {
        "name": "PostgreSQL", "database_type": "relational",
        "environment": "production", "status": "operational",
        "description": "System of record for users, orders and payments.",
    }),
    ("db-redis", {
        "name": "Redis", "database_type": "cache",
        "environment": "production", "status": "operational",
        "description": "Shared cache for sessions, carts and rate limiting.",
    }),
    ("db-mongodb", {
        "name": "MongoDB", "database_type": "document",
        "environment": "production", "status": "operational",
        "description": "Document store for catalog, inventory, invoices and shipping zones.",
    }),
    ("db-elasticsearch", {
        "name": "Elasticsearch", "database_type": "search",
        "environment": "production", "status": "degraded",
        "description": "Full-text product search index.",
    }),
    ("db-clickhouse", {
        "name": "ClickHouse", "database_type": "columnar",
        "environment": "production", "status": "operational",
        "description": "Analytics warehouse for events, metrics and reporting.",
    }),
    ("db-cassandra", {
        "name": "Cassandra", "database_type": "wide-column",
        "environment": "production", "status": "operational",
        "description": "Write-optimised store for the audit log.",
    }),
]

APIS = [
    ("api-stripe", {"name": "Stripe API", "provider": "Stripe", "status": "operational",
                    "description": "Primary card payment processor."}),
    ("api-paypal", {"name": "PayPal API", "provider": "PayPal", "status": "operational",
                    "description": "Alternative wallet checkout."}),
    ("api-sendgrid", {"name": "SendGrid API", "provider": "Twilio SendGrid", "status": "operational",
                      "description": "Transactional email delivery."}),
    ("api-twilio", {"name": "Twilio API", "provider": "Twilio", "status": "operational",
                    "description": "SMS delivery."}),
    ("api-onesignal", {"name": "OneSignal API", "provider": "OneSignal", "status": "operational",
                       "description": "Mobile and web push notifications."}),
    ("api-google-maps", {"name": "Google Maps API", "provider": "Google", "status": "operational",
                         "description": "Address validation and geocoding for shipping quotes."}),
    ("api-recaptcha", {"name": "reCAPTCHA API", "provider": "Google", "status": "operational",
                       "description": "Bot protection on login and signup."}),
    ("api-slack", {"name": "Slack API", "provider": "Slack", "status": "operational",
                   "description": "Report delivery to business channels."}),
]

LIBRARIES = [
    ("lib-react", {"name": "React", "version": "18.3.1", "language": "TypeScript",
                   "description": "UI library for the web frontends."}),
    ("lib-axios", {"name": "Axios", "version": "1.7.2", "language": "TypeScript",
                   "description": "HTTP client used by the Customer Portal."}),
    ("lib-lodash", {"name": "Lodash", "version": "4.17.21", "language": "JavaScript",
                    "description": "Utility functions used in Catalog transformations."}),
    ("lib-pyjwt", {"name": "PyJWT", "version": "2.8.0", "language": "Python",
                   "description": "JWT encoding/decoding in Auth Service."}),
    ("lib-sqlalchemy", {"name": "SQLAlchemy", "version": "2.0.30", "language": "Python",
                        "description": "ORM used by User Profile Service."}),
    ("lib-pydantic", {"name": "Pydantic", "version": "2.7.1", "language": "Python",
                      "description": "Request/response validation for APIs."}),
    ("lib-requests", {"name": "Requests", "version": "2.32.3", "language": "Python",
                      "description": "HTTP client for outbound provider calls."}),
    ("lib-celery", {"name": "Celery", "version": "5.4.0", "language": "Python",
                    "description": "Async task queue workers for notifications."}),
    ("lib-pillow", {"name": "Pillow", "version": "10.3.0", "language": "Python",
                    "description": "Image processing for thumbnail generation."}),
    ("lib-mongoose", {"name": "Mongoose", "version": "8.4.1", "language": "JavaScript",
                      "description": "MongoDB ODM used by Catalog Service."}),
    ("lib-es-client", {"name": "Elasticsearch Client", "version": "8.13.0", "language": "Python",
                       "description": "Official Elasticsearch Python client."}),
    ("lib-stripe-sdk", {"name": "Stripe SDK", "version": "9.12.0", "language": "Python",
                        "description": "Official Stripe Python SDK."}),
]

INFRASTRUCTURE = [
    ("infra-k8s", {"name": "Kubernetes Cluster", "provider": "AWS EKS",
                   "environment": "production", "status": "operational",
                   "description": "Primary container platform for backend services."}),
    ("infra-s3", {"name": "AWS S3", "provider": "AWS",
                  "environment": "production", "status": "operational",
                  "description": "Object storage for product media."}),
    ("infra-lb", {"name": "Load Balancer", "provider": "AWS ALB",
                  "environment": "production", "status": "operational",
                  "description": "Public ingress load balancer in front of the API gateway."}),
    ("infra-cloudfront", {"name": "CloudFront CDN", "provider": "AWS",
                          "environment": "production", "status": "operational",
                          "description": "CDN edge distribution serving the Customer Portal."}),
    ("infra-kafka", {"name": "Kafka Cluster", "provider": "AWS MSK",
                     "environment": "production", "status": "operational",
                     "description": "Event backbone for order and notification events."}),
    ("infra-lambda", {"name": "AWS Lambda", "provider": "AWS",
                      "environment": "production", "status": "operational",
                      "description": "Serverless compute running the Image Service."}),
]

# ---------------------------------------------------------------------------
# Relationships
# ---------------------------------------------------------------------------
# Each entry: (from_id, TYPE, to_id). Direction = "from relies on to".

RELATIONSHIPS = [
    # Customer Portal
    ("svc-customer-portal", "DEPENDS_ON", "svc-checkout"),
    ("svc-customer-portal", "DEPENDS_ON", "svc-catalog"),
    ("svc-customer-portal", "DEPENDS_ON", "svc-search"),
    ("svc-customer-portal", "DEPENDS_ON", "svc-notification"),
    ("svc-customer-portal", "DEPENDS_ON", "svc-user-profile"),
    ("svc-customer-portal", "USES", "lib-react"),
    ("svc-customer-portal", "USES", "lib-axios"),
    ("svc-customer-portal", "DEPLOYED_ON", "infra-cloudfront"),
    ("svc-customer-portal", "OWNED_BY", "team-frontend"),
    # Admin Dashboard
    ("svc-admin-dashboard", "DEPENDS_ON", "svc-reporting"),
    ("svc-admin-dashboard", "DEPENDS_ON", "svc-analytics"),
    ("svc-admin-dashboard", "DEPENDS_ON", "svc-auth"),
    ("svc-admin-dashboard", "USES", "lib-react"),
    ("svc-admin-dashboard", "DEPLOYED_ON", "infra-k8s"),
    ("svc-admin-dashboard", "OWNED_BY", "team-frontend"),
    # Mobile API Gateway
    ("svc-mobile-api-gateway", "DEPENDS_ON", "svc-auth"),
    ("svc-mobile-api-gateway", "DEPENDS_ON", "svc-user-profile"),
    ("svc-mobile-api-gateway", "DEPENDS_ON", "svc-catalog"),
    ("svc-mobile-api-gateway", "DEPENDS_ON", "svc-checkout"),
    ("svc-mobile-api-gateway", "DEPENDS_ON", "infra-lb"),
    ("svc-mobile-api-gateway", "USES", "lib-pydantic"),
    ("svc-mobile-api-gateway", "DEPLOYED_ON", "infra-k8s"),
    ("svc-mobile-api-gateway", "OWNED_BY", "team-devops"),
    # Checkout Service
    ("svc-checkout", "DEPENDS_ON", "svc-payment"),
    ("svc-checkout", "DEPENDS_ON", "svc-cart"),
    ("svc-checkout", "DEPENDS_ON", "svc-order"),
    ("svc-checkout", "DEPENDS_ON", "svc-inventory"),
    ("svc-checkout", "DEPLOYED_ON", "infra-k8s"),
    ("svc-checkout", "OWNED_BY", "team-payments"),
    # Payment Service
    ("svc-payment", "DEPENDS_ON", "svc-auth"),
    ("svc-payment", "DEPENDS_ON", "svc-fraud-detection"),
    ("svc-payment", "DEPENDS_ON", "svc-audit-log"),
    ("svc-payment", "CALLS", "api-stripe"),
    ("svc-payment", "CALLS", "api-paypal"),
    ("svc-payment", "WRITES_TO", "db-postgresql"),
    ("svc-payment", "USES", "lib-pydantic"),
    ("svc-payment", "USES", "lib-stripe-sdk"),
    ("svc-payment", "DEPLOYED_ON", "infra-k8s"),
    ("svc-payment", "OWNED_BY", "team-payments"),
    # Auth Service
    ("svc-auth", "DEPENDS_ON", "svc-session"),
    ("svc-auth", "DEPENDS_ON", "svc-audit-log"),
    ("svc-auth", "READS_FROM", "db-postgresql"),
    ("svc-auth", "READS_FROM", "db-redis"),
    ("svc-auth", "CALLS", "api-recaptcha"),
    ("svc-auth", "USES", "lib-pyjwt"),
    ("svc-auth", "DEPLOYED_ON", "infra-k8s"),
    ("svc-auth", "OWNED_BY", "team-identity"),
    # Session Service
    ("svc-session", "READS_FROM", "db-redis"),
    ("svc-session", "WRITES_TO", "db-redis"),
    ("svc-session", "DEPLOYED_ON", "infra-k8s"),
    ("svc-session", "OWNED_BY", "team-identity"),
    # Fraud Detection Service
    ("svc-fraud-detection", "READS_FROM", "db-redis"),
    ("svc-fraud-detection", "READS_FROM", "db-clickhouse"),
    ("svc-fraud-detection", "DEPLOYED_ON", "infra-k8s"),
    ("svc-fraud-detection", "OWNED_BY", "team-payments"),
    # Audit Log Service
    ("svc-audit-log", "WRITES_TO", "db-cassandra"),
    ("svc-audit-log", "DEPLOYED_ON", "infra-k8s"),
    ("svc-audit-log", "OWNED_BY", "team-platform"),
    # Notification Service
    ("svc-notification", "DEPENDS_ON", "svc-user-profile"),
    ("svc-notification", "DEPENDS_ON", "infra-kafka"),
    ("svc-notification", "CALLS", "api-sendgrid"),
    ("svc-notification", "CALLS", "api-twilio"),
    ("svc-notification", "CALLS", "api-onesignal"),
    ("svc-notification", "USES", "lib-requests"),
    ("svc-notification", "USES", "lib-celery"),
    ("svc-notification", "DEPLOYED_ON", "infra-k8s"),
    ("svc-notification", "OWNED_BY", "team-notifications"),
    # User Profile Service
    ("svc-user-profile", "READS_FROM", "db-postgresql"),
    ("svc-user-profile", "WRITES_TO", "db-postgresql"),
    ("svc-user-profile", "USES", "lib-sqlalchemy"),
    ("svc-user-profile", "DEPLOYED_ON", "infra-k8s"),
    ("svc-user-profile", "OWNED_BY", "team-identity"),
    # Cart Service
    ("svc-cart", "READS_FROM", "db-redis"),
    ("svc-cart", "WRITES_TO", "db-redis"),
    ("svc-cart", "DEPLOYED_ON", "infra-k8s"),
    ("svc-cart", "OWNED_BY", "team-platform"),
    # Order Service
    ("svc-order", "DEPENDS_ON", "svc-notification"),
    ("svc-order", "DEPENDS_ON", "svc-invoice"),
    ("svc-order", "DEPENDS_ON", "svc-shipping"),
    ("svc-order", "DEPENDS_ON", "infra-kafka"),
    ("svc-order", "READS_FROM", "db-postgresql"),
    ("svc-order", "WRITES_TO", "db-postgresql"),
    ("svc-order", "DEPLOYED_ON", "infra-k8s"),
    ("svc-order", "OWNED_BY", "team-platform"),
    # Invoice Service
    ("svc-invoice", "WRITES_TO", "db-mongodb"),
    ("svc-invoice", "DEPLOYED_ON", "infra-k8s"),
    ("svc-invoice", "OWNED_BY", "team-payments"),
    # Inventory Service
    ("svc-inventory", "READS_FROM", "db-mongodb"),
    ("svc-inventory", "WRITES_TO", "db-mongodb"),
    ("svc-inventory", "DEPLOYED_ON", "infra-k8s"),
    ("svc-inventory", "OWNED_BY", "team-platform"),
    # Catalog Service
    ("svc-catalog", "DEPENDS_ON", "svc-image"),
    ("svc-catalog", "READS_FROM", "db-mongodb"),
    ("svc-catalog", "USES", "lib-mongoose"),
    ("svc-catalog", "USES", "lib-lodash"),
    ("svc-catalog", "DEPLOYED_ON", "infra-k8s"),
    ("svc-catalog", "OWNED_BY", "team-platform"),
    # Image Service
    ("svc-image", "DEPENDS_ON", "infra-s3"),
    ("svc-image", "USES", "lib-pillow"),
    ("svc-image", "DEPLOYED_ON", "infra-lambda"),
    ("svc-image", "OWNED_BY", "team-platform"),
    # Search Service
    ("svc-search", "READS_FROM", "db-elasticsearch"),
    ("svc-search", "USES", "lib-es-client"),
    ("svc-search", "DEPLOYED_ON", "infra-k8s"),
    ("svc-search", "OWNED_BY", "team-platform"),
    # Recommendation Service
    ("svc-recommendation", "DEPENDS_ON", "svc-user-profile"),
    ("svc-recommendation", "DEPENDS_ON", "svc-catalog"),
    ("svc-recommendation", "READS_FROM", "db-clickhouse"),
    ("svc-recommendation", "DEPLOYED_ON", "infra-k8s"),
    ("svc-recommendation", "OWNED_BY", "team-data"),
    # Analytics Service
    ("svc-analytics", "READS_FROM", "db-postgresql"),
    ("svc-analytics", "READS_FROM", "db-clickhouse"),
    ("svc-analytics", "DEPLOYED_ON", "infra-k8s"),
    ("svc-analytics", "OWNED_BY", "team-data"),
    # Reporting Service
    ("svc-reporting", "READS_FROM", "db-clickhouse"),
    ("svc-reporting", "READS_FROM", "db-postgresql"),
    ("svc-reporting", "CALLS", "api-slack"),
    ("svc-reporting", "DEPLOYED_ON", "infra-k8s"),
    ("svc-reporting", "OWNED_BY", "team-data"),
    # Shipping Service
    ("svc-shipping", "CALLS", "api-google-maps"),
    ("svc-shipping", "READS_FROM", "db-mongodb"),
    ("svc-shipping", "DEPLOYED_ON", "infra-k8s"),
    ("svc-shipping", "OWNED_BY", "team-platform"),
]

# ---------------------------------------------------------------------------
# Normalised structures + validation
# ---------------------------------------------------------------------------

LABELS = {
    **{nid: "Team" for nid, _ in TEAMS},
    **{nid: "Service" for nid, _ in SERVICES},
    **{nid: "Database" for nid, _ in DATABASES},
    **{nid: "API" for nid, _ in APIS},
    **{nid: "Library" for nid, _ in LIBRARIES},
    **{nid: "Infrastructure" for nid, _ in INFRASTRUCTURE},
}

ALL_PROPERTIES = {}
for _group in (TEAMS, SERVICES, DATABASES, APIS, LIBRARIES, INFRASTRUCTURE):
    for _nid, _props in _group:
        ALL_PROPERTIES[_nid] = dict(_props)


def _detect_service_cycles() -> bool:
    adjacency: dict[str, list[str]] = {}
    for src, rtype, dst in RELATIONSHIPS:
        if LABELS.get(src) == "Service" and LABELS.get(dst) == "Service":
            adjacency.setdefault(src, []).append(dst)
    visiting, done = set(), set()

    def visit(node: str) -> bool:
        if node in done:
            return True
        if node in visiting:
            return False
        visiting.add(node)
        ok = all(visit(nxt) for nxt in adjacency.get(node, []))
        visiting.discard(node)
        done.add(node)
        return ok

    return all(visit(n) for n in list(adjacency))


def validate() -> None:
    assert len(ALL_PROPERTIES) == len(LABELS), "duplicate node ids"
    assert _detect_service_cycles(), "service dependency graph must be acyclic"
    known_types = set(DEPENDENCY_TYPES) | {"OWNED_BY"}
    for src, rtype, dst in RELATIONSHIPS:
        assert src in LABELS, f"unknown relationship source: {src}"
        assert dst in LABELS, f"unknown relationship target: {dst}"
        assert rtype in known_types, f"unknown relationship type: {rtype}"
    # Ownership integrity: every service is owned by exactly one team.
    owners = {}
    for src, rtype, dst in RELATIONSHIPS:
        if rtype == "OWNED_BY":
            assert LABELS[dst] == "Team"
            owners.setdefault(src, set()).add(dst)
    for sid, _ in SERVICES:
        assert len(owners.get(sid, [])) == 1, f"{sid} must have exactly one owner"


validate()

NODE_COUNT = len(ALL_PROPERTIES)
REL_COUNT = len(RELATIONSHIPS)
