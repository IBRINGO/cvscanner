"""File storage abstraction (section 35 of the Phase 2 brief).

`Document.storage_reference` (apps/documents/models.py) holds whatever a
FileStorage implementation returns from `save()` - the domain/application
layers never know if that's a local filesystem path or an S3 key.
"""
from typing import Protocol


class FileStorage(Protocol):
    def save(self, content: bytes, key: str) -> str:
        """Persists `content` under (or derived from) `key`. Returns the
        storage reference to keep on the Document record - not
        necessarily equal to `key` (e.g. a storage backend might prefix
        it), so callers must persist the return value, not `key` itself.
        """
        ...

    def read(self, reference: str) -> bytes:
        """Raises FileNotFoundError if `reference` does not exist."""
        ...

    def delete(self, reference: str) -> None:
        """No-op if `reference` does not exist."""
        ...
