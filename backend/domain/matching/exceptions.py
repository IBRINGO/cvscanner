class AnalysisValidationError(Exception):
    """Raised when an analysis cannot be created or run - e.g. a
    referenced document is the wrong type, not yet processed, or its
    structured profile is missing. Mirrors
    domain.documents.exceptions.DocumentValidationError's role: caught by
    the application layer and turned into a safe, user-facing message,
    never a raw traceback.
    """
