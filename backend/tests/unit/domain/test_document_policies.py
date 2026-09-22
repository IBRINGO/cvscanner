import pytest

from domain.documents.enums import ProcessingStatus
from domain.documents.exceptions import DocumentValidationError
from domain.documents.policies import can_transition, validate_file


class TestValidateFile:
    def test_accepts_a_valid_pdf(self):
        validate_file(filename="cv.pdf", mime_type="application/pdf", size_bytes=1024)

    def test_accepts_a_valid_docx(self):
        validate_file(
            filename="cv.docx",
            mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            size_bytes=1024,
        )

    def test_rejects_empty_file(self):
        with pytest.raises(DocumentValidationError, match="empty"):
            validate_file(filename="cv.pdf", mime_type="application/pdf", size_bytes=0)

    def test_rejects_file_over_size_limit(self):
        with pytest.raises(DocumentValidationError, match="exceeds"):
            validate_file(filename="cv.pdf", mime_type="application/pdf", size_bytes=11 * 1024 * 1024)

    def test_rejects_unsupported_mime_type(self):
        with pytest.raises(DocumentValidationError, match="Unsupported file type"):
            validate_file(filename="cv.exe", mime_type="application/x-msdownload", size_bytes=1024)

    def test_rejects_mismatched_extension(self):
        with pytest.raises(DocumentValidationError, match="extension"):
            validate_file(filename="cv.docx", mime_type="application/pdf", size_bytes=1024)


class TestStatusTransitions:
    def test_uploaded_can_move_to_validating(self):
        assert can_transition(ProcessingStatus.UPLOADED, ProcessingStatus.VALIDATING)

    def test_uploaded_cannot_jump_to_processed(self):
        assert not can_transition(ProcessingStatus.UPLOADED, ProcessingStatus.PROCESSED)

    def test_failed_can_restart_from_validating(self):
        assert can_transition(ProcessingStatus.FAILED, ProcessingStatus.VALIDATING)

    def test_processed_cannot_move_directly_to_failed(self):
        # Reprocessing must go through PROCESSING again, not jump straight
        # from a finished state to a failed one.
        assert not can_transition(ProcessingStatus.PROCESSED, ProcessingStatus.FAILED)

    def test_same_state_transition_is_a_noop_allowed(self):
        assert can_transition(ProcessingStatus.PROCESSING, ProcessingStatus.PROCESSING)
