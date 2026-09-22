# interfaces/api/common

Reserved for cross-cutting API concerns once there is more than one
resource to share them: `pagination.py`, `exceptions.py` (a DRF custom
exception handler), `permissions.py`, `responses.py` (a consistent
success/error envelope). Phase 1's single endpoint (`health/`) doesn't need
any of these yet — DRF's defaults are enough — so nothing is implemented
here to avoid building abstractions with no real caller.
