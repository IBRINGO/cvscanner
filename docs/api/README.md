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

As new endpoints land, document them here (or generate an OpenAPI schema —
not yet configured in Phase 1) grouped by resource: `auth/`, `cvs/`,
`jobs/`, `analyses/`, `recommendations/`, `tailoring/`.
