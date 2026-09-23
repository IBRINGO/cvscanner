# API Documentation

This folder will hold the CVScanner REST API reference as endpoints are
built out (Phase 2 onward: CVs, jobs, analyses, recommendations, tailoring).

For Phase 1, the only available endpoint is:

## `GET /api/v1/health/`

Liveness/readiness check used by the frontend to confirm the backend is
reachable.

**Response `200 OK`:**

```json
{
  "status": "ok",
  "service": "cvscanner-backend",
  "version": "0.1.0"
}
```

No authentication is required for this endpoint.

The full CVs/jobs/skills/analyses/recommendations/tailoring endpoint
table lives in the root [README.md](../../README.md#api) (kept in one
place to avoid two copies drifting apart). For the Phase 4 analyses
endpoints specifically - request/response shapes, the matching engine's
evidence hierarchy, and scoring - see
[docs/architecture/phase-4-matching.md](../architecture/phase-4-matching.md).
For the Phase 5 recommendations/tailoring endpoints - request/response
shapes, the recommendation engine, and the Truth Layer every generated
change passes through - see
[docs/architecture/phase-5-recommendations-and-tailoring.md](../architecture/phase-5-recommendations-and-tailoring.md).

As new endpoints land, document them in the root README's table (or
generate an OpenAPI schema - not yet configured) grouped by resource:
`auth/`, `cvs/`, `jobs/`, `skills/`, `analyses/`, `recommendations/`,
`tailoring/`.
