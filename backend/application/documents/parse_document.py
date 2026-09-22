"""Parse use case (section 10-12 of the Phase 2 brief).

    repository needs:      get_storage_reference(document_id) -> str
    storage needs:          read(reference) -> bytes
    parser_registry needs:  get_parser(mime_type) -> DocumentParser

Deliberately does not persist anything itself - see
application/cv/process_pipeline.py, which also runs section detection
before saving the parsed result, so persistence happens once with the
complete picture rather than in two separate writes.
"""
from domain.documents.entities import ParsedDocument


class ParseDocument:
    def __init__(self, repository, storage, parser_registry) -> None:
        self._repository = repository
        self._storage = storage
        self._parser_registry = parser_registry

    def execute(self, document_id: str, mime_type: str, filename: str) -> ParsedDocument:
        reference = self._repository.get_storage_reference(document_id)
        content = self._storage.read(reference)
        parser = self._parser_registry.get_parser(mime_type)
        return parser.parse(content, filename)
