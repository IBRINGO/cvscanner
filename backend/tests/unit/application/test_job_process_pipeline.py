"""Mirrors test_process_pipeline.py for ProcessJobDocumentPipeline - see
that file for the enrichment-isolation rationale (Phase 3 sections 62/80).
"""
import dataclasses

from application.jobs.process_pipeline import ProcessJobDocumentPipeline
from domain.documents.entities import DocumentRecord, ParsedDocument
from domain.documents.enums import DocumentType, ProcessingStatus
from domain.documents.exceptions import DocumentParsingError
from domain.job.entities import JobProfile
from domain.skills.enrichment import TechnologyMentionScanner


def _record(status=ProcessingStatus.UPLOADED) -> DocumentRecord:
    return DocumentRecord(
        id="job-1",
        owner_id=None,
        document_type=DocumentType.JOB_OFFER,
        original_filename="job.txt",
        mime_type="text/plain",
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
        self.failure_reason = None

    def get(self, document_id):
        return self.record

    def update_status(self, document_id, status):
        self.status_history.append(status)
        self.record = dataclasses.replace(self.record, status=status)

    def save_parsed_result(self, document_id, *, raw_text, page_count, sections):
        pass

    def update_processing_metadata(self, document_id, **fields):
        pass

    def mark_failed(self, document_id, error_message):
        self.failure_reason = error_message
        self.status_history.append(ProcessingStatus.FAILED)
        self.record = dataclasses.replace(self.record, status=ProcessingStatus.FAILED)


class FakeParseDocument:
    def __init__(self, error=None):
        self._error = error

    def execute(self, document_id, mime_type, filename):
        if self._error:
            raise self._error
        return ParsedDocument(raw_text="Backend Engineer\n\nREQUIREMENTS\n3+ years of Python")


class FakeExtractJobProfile:
    def execute(self, document_id, parsed, sections):
        return JobProfile(
            title=None,
            company=None,
            location=None,
            employment_type=None,
            seniority=None,
            summary=None,
        )


class FakeEnrichJobProfile:
    def __init__(self, error=None):
        self.called = False
        self._error = error

    def execute(self, document_id, profile, scanner):
        if self._error:
            raise self._error
        self.called = True


class FakeGenerateEmbeddings:
    def __init__(self, error=None):
        self.called = False
        self._error = error

    def execute(self, entity_type, entity_id, text):
        if self._error:
            raise self._error
        self.called = True


def _build_pipeline(repository, parse_document, extract, enrich=None, embeddings=None):
    return ProcessJobDocumentPipeline(
        repository,
        parse_document,
        extract,
        enrich or FakeEnrichJobProfile(),
        embeddings or FakeGenerateEmbeddings(),
        TechnologyMentionScanner(()),
    )


class TestProcessJobDocumentPipeline:
    def test_happy_path_transitions_to_processed_and_runs_enrichment(self):
        repository = FakeDocumentRepository()
        enrich = FakeEnrichJobProfile()
        embeddings = FakeGenerateEmbeddings()
        pipeline = _build_pipeline(
            repository, FakeParseDocument(), FakeExtractJobProfile(), enrich, embeddings
        )

        pipeline.run("job-1")

        assert repository.record.status == ProcessingStatus.PROCESSED
        assert enrich.called
        assert embeddings.called

    def test_already_processed_is_skipped(self):
        repository = FakeDocumentRepository(initial_status=ProcessingStatus.PROCESSED)
        pipeline = _build_pipeline(repository, FakeParseDocument(), FakeExtractJobProfile())

        pipeline.run("job-1")

        assert repository.status_history == []

    def test_parsing_error_marks_failed_without_raising(self):
        repository = FakeDocumentRepository()
        pipeline = _build_pipeline(
            repository, FakeParseDocument(error=DocumentParsingError("bad file")), FakeExtractJobProfile()
        )

        pipeline.run("job-1")

        assert repository.record.status == ProcessingStatus.FAILED
        assert repository.failure_reason == "bad file"

    def test_enrichment_failure_does_not_fail_the_document(self):
        repository = FakeDocumentRepository()
        enrich = FakeEnrichJobProfile(error=RuntimeError("boom"))
        pipeline = _build_pipeline(repository, FakeParseDocument(), FakeExtractJobProfile(), enrich=enrich)

        pipeline.run("job-1")  # must not raise

        assert repository.record.status == ProcessingStatus.PROCESSED

    def test_embedding_failure_does_not_fail_the_document(self):
        repository = FakeDocumentRepository()
        embeddings = FakeGenerateEmbeddings(error=RuntimeError("boom"))
        pipeline = _build_pipeline(
            repository, FakeParseDocument(), FakeExtractJobProfile(), embeddings=embeddings
        )

        pipeline.run("job-1")  # must not raise

        assert repository.record.status == ProcessingStatus.PROCESSED
