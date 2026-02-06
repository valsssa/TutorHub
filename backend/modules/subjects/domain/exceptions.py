"""
Domain exceptions for subjects module.

These exceptions represent business rule violations specific to subjects.
"""


class SubjectError(Exception):
    """Base exception for subject domain errors."""

    pass


class SubjectNotFoundError(SubjectError):
    """Raised when a subject is not found."""

    def __init__(self, identifier: int | str | None = None):
        self.identifier = identifier
        message = f"Subject not found: {identifier}" if identifier else "Subject not found"
        super().__init__(message)


class DuplicateSubjectError(SubjectError):
    """Raised when attempting to create a subject with a name that already exists."""

    def __init__(self, name: str):
        self.name = name
        super().__init__(f"Subject already exists: {name}")


class SubjectInUseError(SubjectError):
    """Raised when attempting to delete a subject that is still in use by tutors."""

    def __init__(self, subject_id: int, tutor_count: int | None = None):
        self.subject_id = subject_id
        self.tutor_count = tutor_count
        if tutor_count:
            message = f"Subject {subject_id} cannot be deleted: {tutor_count} tutor(s) still teach it"
        else:
            message = f"Subject {subject_id} cannot be deleted: it is still in use"
        super().__init__(message)


class InvalidSubjectDataError(SubjectError):
    """Raised when subject data is invalid."""

    def __init__(self, field: str, reason: str):
        self.field = field
        self.reason = reason
        super().__init__(f"Invalid subject {field}: {reason}")
