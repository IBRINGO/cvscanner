# interfaces/api/common

Reserved for cross-cutting API concerns: `pagination.py`, `exceptions.py`
(a DRF custom exception handler), `permissions.py`, `responses.py` (a
consistent success/error envelope).

Phase 2 added `cvs/` and `jobs/`, whose views/serializers are
structurally similar (list/create/status/profile, each scoped to a
`document_type`). They are still small and independently readable as
plain DRF `APIView` classes - extracting a shared base class or generic
viewset now would save roughly a dozen lines per resource at the cost of
an extra layer of indirection for a reader trying to find "what does
`POST /cvs/` actually do." Revisit this once a third document-backed
resource needs the same shape, or once the duplication itself becomes
the source of bugs (e.g. one resource's validation drifting from the
other's).

Phase 3 added `skills/` - a read-only resource with a different shape
(list + one detail lookup by name, no upload/status/profile) - so it
was not folded into the same "would a shared base class help" question
above.
