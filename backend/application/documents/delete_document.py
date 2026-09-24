"""Delete-document use case (CVs and job offers alike).

    repository needs:          get(document_id) -> DocumentRecord,
                                get_storage_reference(document_id) -> str,
                                delete(document_id) -> None
    storage needs:              delete(reference) -> None
    semantic_repository needs:  delete_for_entity(entity_type, entity_id) -> None

Deleting a document is the one place a candidate/recruiter can "start
over" with the exact same file - re-uploading it afterwards is treated
as a brand new upload (a fresh sha256-keyed storage object, a fresh
Document row), not a duplicate reusing stale processing results, since
the old row and everything derived from it (structured profile,
analyses run against it, recommendations, tailoring plans - see
apps/*/models.py's on_delete=CASCADE graph) is genuinely gone.

Only SemanticRepresentation needs explicit cleanup here: it is keyed by
a loose (entity_type, entity_id) pair, not a real foreign key (see
domain/semantics - a semantic entity is a fact, not a document section),
so it never cascades on its own. Everything else cascades at the
database level the moment the Document row is deleted.
"""
from domain.documents.enums import DocumentType
from domain.semantics.enums import SemanticEntityType

_PROFILE_ENTITY_TYPE = {
    DocumentType.CV: SemanticEntityType.CANDIDATE_PROFILE,
    DocumentType.JOB_OFFER: SemanticEntityType.JOB_PROFILE,
}


class DeleteDocument:
    def __init__(self, repository, storage, semantic_repository) -> None:
        self._repository = repository
        self._storage = storage
        self._semantic_repository = semantic_repository

    def execute(self, document_id: str) -> None:
        document = self._repository.get(document_id)
        storage_reference = self._repository.get_storage_reference(document_id)

        entity_type = _PROFILE_ENTITY_TYPE[document.document_type]
        self._semantic_repository.delete_for_entity(entity_type, document_id)

        self._repository.delete(document_id)
        self._storage.delete(storage_reference)
