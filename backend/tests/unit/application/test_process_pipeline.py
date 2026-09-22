"""Tests ProcessCvDocumentPipeline's orchestration/error-handling logic
against fake dependencies - no Django, no database, no real parsing.
"""
import dataclasses

import pytest

from application.cv.process_pipeline import ProcessCvDocumentPipeline
from domain.documents.entities import DocumentRecord, ParsedDocument
from domain.documents.enums import DocumentType, ProcessingStatus
from domain.documents.exceptions import DocumentParsingError


def _record(status=ProcessingStatus.UPLOADED) -> DocumentRecord:
    return DocumentRecord(
        id="doc-1",
        owner_id=None,
        document_type=DocumentType.CV,
        original_filename="cv.pdf",
        mime_type="application/pdf",
        file_size=100,
        file_hash="abc",
        status=status,
        page_count=None,
        processing_metadata={},
        created_at=None,
        updated_at=None,
    )


class FakeDocumentRepository:
    def __init__(self, initial_status=ProcessingStatus.UPLOADED):
        self.record = _record(initial_status)
        self.status_history = []
        self.saved_parsed_result = None
        self.metadata_updates = {}
        self.failure_reason = None

    def get(self, document_id):
        return self.record

    def update_status(self, document_id, status):
        self.status_history.append(status)
        self.record = dataclasses.replace(self.record, status=status)

    def save_parsed_result(self, document_id, *, raw_text, page_count, sections):
        self.saved_parsed_result = {"raw_text": raw_text, "page_count": page_count, "sections": sections}

    def update_processing_metadata(self, document_id, **fields):
        self.metadata_updates.update(fields)

    def mark_failed(self, document_id, error_message):
        self.failure_reason = error_message
        self.status_history.append(ProcessingStatus.FAILED)
        self.record = dataclasses.replace(self.record, status=ProcessingStatus.FAILED)


class FakeParseDocument:
    def __init__(self, parsed=None, error=None):
        self._parsed = parsed or ParsedDocument(raw_text="SKILLS\nPython")
        self._error = error

    def execute(self, document_id, mime_type, filename):
        if self._error:
            raise self._error
        return self._parsed


class FakeExtractCandidateProfile:
    def __init__(self):
        self.called_with = None

    def execute(self, document_id, parsed, sections):
        self.called_with = (document_id, parsed, sections)
        return object()


class TestProcessCvDocumentPipelineSuccess:
    def test_happy_path_transitions_to_processed(self):
        repository = FakeDocumentRepository()
        pipeline = ProcessCvDocumentPipeline(repository, FakeParseDocument(), FakeExtractCandidateProfile())

        pipeline.run("doc-1")

        assert repository.record.status == ProcessingStatus.PROCESSED
        assert repository.status_history == [
            ProcessingStatus.VALIDATING,
            ProcessingStatus.PROCESSING,
            ProcessingStatus.PROCESSED,
        ]
        assert repository.metadata_updates.get("extraction_version")

    def test_saves_parsed_text_and_sections(self):
        repository = FakeDocumentRepository()
        parsed = ParsedDocument(raw_text="SUMMARY\nSomething\n\nSKILLS\nPython")
        pipeline = ProcessCvDocumentPipeline(
            repository, FakeParseDocument(parsed), FakeExtractCandidateProfile()
        )

        pipeline.run("doc-1")

        assert repository.saved_parsed_result["raw_text"] == parsed.raw_text
        assert len(repository.saved_parsed_result["sections"]) >= 1


class TestProcessCvDocumentPipelineIdempotency:
    def test_already_processed_document_is_skipped(self):
        repository = FakeDocumentRepository(initial_status=ProcessingStatus.PROCESSED)
        extract = FakeExtractCandidateProfile()
        pipeline = ProcessCvDocumentPipeline(repository, FakeParseDocument(), extract)

        pipeline.run("doc-1")

        assert repository.status_history == []  # no transitions attempted
        assert extract.called_with is None  # extraction never ran again


class TestProcessCvDocumentPipelineFailure:
    def test_parsing_error_marks_document_failed_without_raising(self):
        repository = FakeDocumentRepository()
        pipeline = ProcessCvDocumentPipeline(
            repository,
            FakeParseDocument(error=DocumentParsingError("corrupted file")),
            FakeExtractCandidateProfile(),
        )

        pipeline.run("doc-1")  # must not raise

        assert repository.record.status == ProcessingStatus.FAILED
        assert repository.failure_reason == "corrupted file"

    def test_unexpected_error_marks_failed_with_safe_message_and_reraises(self):
        repository = FakeDocumentRepository()

        class BoomParseDocument:
            def execute(self, *args, **kwargs):
                raise RuntimeError("database connection lost: secret-token-xyz")

        pipeline = ProcessCvDocumentPipeline(repository, BoomParseDocument(), FakeExtractCandidateProfile())

        with pytest.raises(RuntimeError):
            pipeline.run("doc-1")

        assert repository.record.status == ProcessingStatus.FAILED
        # The safe, generic message is stored - not the raw exception text,
        # which could leak internal details (section 30 of the brief).
        assert "secret-token-xyz" not in repository.failure_reason
