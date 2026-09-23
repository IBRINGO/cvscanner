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
from django.conf import settings

from application.cv.extract_candidate_profile import ExtractCandidateProfile
from application.cv.process_pipeline import ProcessCvDocumentPipeline
from application.documents.parse_document import ParseDocument
from application.documents.upload_document import UploadDocument
from application.jobs.extract_job_profile import ExtractJobProfile
from application.jobs.process_pipeline import ProcessJobDocumentPipeline
from application.matching.create_analysis import CreateAnalysis
from application.matching.run_analysis import RunAnalysis
from application.semantics.enrich_candidate_profile import EnrichCandidateProfile
from application.semantics.enrich_job_profile import EnrichJobProfile
from application.semantics.generate_embeddings import GenerateSemanticEmbeddings
from domain.matching.weights import MATCHING_ENGINE_VERSION
from domain.skills.enrichment import TechnologyMentionScanner
from infrastructure.database.repositories.analysis_repository import DjangoAnalysisRepository
from infrastructure.database.repositories.candidate_profile_repository import (
    DjangoCandidateEnrichmentRepository,
    DjangoCandidateProfileRepository,
)
from infrastructure.database.repositories.document_repository import DjangoDocumentRepository
from infrastructure.database.repositories.job_profile_repository import (
    DjangoJobEnrichmentRepository,
    DjangoJobProfileRepository,
)
from infrastructure.database.repositories.semantic_representation_repository import (
    DjangoSemanticRepresentationRepository,
)
from infrastructure.database.repositories.skill_repository import DjangoSkillRepository
from infrastructure.document_processing.extraction.candidate_extractor import (
    RuleBasedCandidateExtractor,
)
from infrastructure.document_processing.extraction.job_extractor import RuleBasedJobExtractor
from infrastructure.document_processing.parsers.registry import DocumentParserRegistry
from infrastructure.embeddings.base import EmbeddingProvider
from infrastructure.embeddings.providers.fake_provider import FakeEmbeddingProvider
from infrastructure.embeddings.providers.fallback_provider import FallbackEmbeddingProvider
from infrastructure.embeddings.providers.gemini_provider import GeminiEmbeddingProvider
from infrastructure.embeddings.providers.openai_provider import OpenAIEmbeddingProvider
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


def build_embedding_provider() -> EmbeddingProvider:
    """Embeddings are optional (Phase 3 section 25, Phase 4 section 29).
    Gemini is the primary provider, OpenAI the fallback - if
    GEMINI_API_KEY fails, or is not configured, OpenAI is tried; if
    neither key is configured (or both fail), the deterministic,
    network-free FakeEmbeddingProvider keeps the pipeline fully usable
    without any external service.
    """
    real_providers: list[EmbeddingProvider] = []

    gemini_key = getattr(settings, "GEMINI_API_KEY", "")
    if gemini_key:
        gemini = GeminiEmbeddingProvider(api_key=gemini_key, model=settings.GEMINI_EMBEDDING_MODEL)
        real_providers.append(gemini)

    openai_key = getattr(settings, "OPENAI_API_KEY", "")
    if openai_key:
        real_providers.append(OpenAIEmbeddingProvider(api_key=openai_key, model=settings.EMBEDDING_MODEL))

    if not real_providers:
        return FakeEmbeddingProvider()
    if len(real_providers) == 1:
        return real_providers[0]
    return FallbackEmbeddingProvider(real_providers)


def build_technology_scanner() -> TechnologyMentionScanner:
    return TechnologyMentionScanner(DjangoSkillRepository().all())


def build_cv_processing_pipeline() -> ProcessCvDocumentPipeline:
    skill_alias_index = DjangoSkillRepository().alias_index()
    extractor = RuleBasedCandidateExtractor(skill_alias_index)
    extract_use_case = ExtractCandidateProfile(
        extractor=extractor, repository=DjangoCandidateProfileRepository()
    )
    enrich_use_case = EnrichCandidateProfile(repository=DjangoCandidateEnrichmentRepository())
    generate_embeddings = GenerateSemanticEmbeddings(
        provider=build_embedding_provider(), repository=DjangoSemanticRepresentationRepository()
    )
    return ProcessCvDocumentPipeline(
        document_repository=build_document_repository(),
        parse_document=build_parse_document(),
        extract_candidate_profile=extract_use_case,
        enrich_candidate_profile=enrich_use_case,
        generate_embeddings=generate_embeddings,
        technology_scanner=build_technology_scanner(),
    )


def build_job_processing_pipeline() -> ProcessJobDocumentPipeline:
    skill_alias_index = DjangoSkillRepository().alias_index()
    extractor = RuleBasedJobExtractor(skill_alias_index)
    extract_use_case = ExtractJobProfile(extractor=extractor, repository=DjangoJobProfileRepository())
    enrich_use_case = EnrichJobProfile(repository=DjangoJobEnrichmentRepository())
    generate_embeddings = GenerateSemanticEmbeddings(
        provider=build_embedding_provider(), repository=DjangoSemanticRepresentationRepository()
    )
    return ProcessJobDocumentPipeline(
        document_repository=build_document_repository(),
        parse_document=build_parse_document(),
        extract_job_profile=extract_use_case,
        enrich_job_profile=enrich_use_case,
        generate_embeddings=generate_embeddings,
        technology_scanner=build_technology_scanner(),
    )


def build_analysis_repository() -> DjangoAnalysisRepository:
    return DjangoAnalysisRepository()


def build_create_analysis() -> CreateAnalysis:
    return CreateAnalysis(
        document_repository=build_document_repository(),
        analysis_repository=build_analysis_repository(),
        engine_version=MATCHING_ENGINE_VERSION,
    )


def build_run_analysis() -> RunAnalysis:
    return RunAnalysis(
        candidate_profile_repository=DjangoCandidateProfileRepository(),
        job_profile_repository=DjangoJobProfileRepository(),
        skill_repository=DjangoSkillRepository(),
        analysis_repository=build_analysis_repository(),
        embedding_provider=build_embedding_provider(),
        engine_version=MATCHING_ENGINE_VERSION,
    )
