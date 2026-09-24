from pathlib import Path

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

FIXTURES_DIR = Path(__file__).parents[2] / "fixtures"


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def cv_pdf_bytes():
    return (FIXTURES_DIR / "sample_cv.pdf").read_bytes()


@pytest.fixture
def cv_docx_bytes():
    return (FIXTURES_DIR / "sample_cv.docx").read_bytes()


@pytest.fixture
def corrupted_pdf_bytes():
    return (FIXTURES_DIR / "corrupted.pdf").read_bytes()


@pytest.fixture
def unsupported_bytes():
    return (FIXTURES_DIR / "unsupported.exe").read_bytes()


@pytest.fixture
def fixture_bytes():
    def _read(name: str) -> bytes:
        return (FIXTURES_DIR / name).read_bytes()

    return _read


def make_upload(name: str, content: bytes, content_type: str) -> SimpleUploadedFile:
    return SimpleUploadedFile(name, content, content_type=content_type)
