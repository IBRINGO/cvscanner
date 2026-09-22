"""Composition root (see docs/architecture/dependency-rule.md).

This is the ONLY place allowed to import both application/* use cases and
concrete infrastructure/* implementations. interfaces/api views and
workers/tasks both call these factory functions instead of constructing
use cases themselves - that keeps views and tasks thin, and keeps
application/domain code from ever importing Django, Celery, or a parsing
library directly.

Nothing here is cached at import time (each call builds fresh objects) -
these are cheap to construct (no I/O happens until a method is called),
and per-request construction avoids any shared-state surprises between
requests/tasks.
"""
from application.cv.extract_candidate_profile import ExtractCandidateProfile
from application.cv.process_pipeline import ProcessCvDocumentPipeline
from application.documents.parse_document import ParseDocument
from application.documents.upload_document import UploadDocument
from application.jobs.extract_job_profile import ExtractJobProfile
from application.jobs.process_pipeline import ProcessJobDocumentPipeline
from infrastructure.database.repositories.candidate_profile_repository import (
    DjangoCandidateProfileRepository,
)
from infrastructure.database.repositories.document_repository import DjangoDocumentRepository
from infrastructure.database.repositories.job_profile_repository import DjangoJobProfileRepository
from infrastructure.database.repositories.skill_repository import DjangoSkillRepository
from infrastructure.document_processing.extraction.candidate_extractor import (
    RuleBasedCandidateExtractor,
)
from infrastructure.document_processing.extraction.job_extractor import RuleBasedJobExtractor
from infrastructure.document_processing.parsers.registry import DocumentParserRegistry
from infrastructure.storage.local import LocalFileStorage


def build_document_repository() -> DjangoDocumentRepository:
    return DjangoDocumentRepository()


def build_file_storage() -> LocalFileStorage:
    return LocalFileStorage()


def build_upload_document() -> UploadDocument:
    return UploadDocument(repository=build_document_repository(), storage=build_file_storage())


def build_parse_document() -> ParseDocument:
    return ParseDocument(
        repository=build_document_repository(),
        storage=build_file_storage(),
        parser_registry=DocumentParserRegistry(),
    )


def build_cv_processing_pipeline() -> ProcessCvDocumentPipeline:
    skill_alias_index = DjangoSkillRepository().alias_index()
    extractor = RuleBasedCandidateExtractor(skill_alias_index)
    extract_use_case = ExtractCandidateProfile(
        extractor=extractor, repository=DjangoCandidateProfileRepository()
    )
    return ProcessCvDocumentPipeline(
        document_repository=build_document_repository(),
        parse_document=build_parse_document(),
        extract_candidate_profile=extract_use_case,
    )


def build_job_processing_pipeline() -> ProcessJobDocumentPipeline:
    skill_alias_index = DjangoSkillRepository().alias_index()
    extractor = RuleBasedJobExtractor(skill_alias_index)
    extract_use_case = ExtractJobProfile(extractor=extractor, repository=DjangoJobProfileRepository())
    return ProcessJobDocumentPipeline(
        document_repository=build_document_repository(),
        parse_document=build_parse_document(),
        extract_job_profile=extract_use_case,
    )
