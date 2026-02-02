"""
Domain exceptions for students module.

These exceptions represent business rule violations specific to student operations.
"""


class StudentError(Exception):
    """Base exception for student domain errors."""

    pass


class StudentNotFoundError(StudentError):
    """Raised when a student user is not found."""

    def __init__(self, identifier: str | int | None = None):
        self.identifier = identifier
        if identifier:
            message = f"Student not found: {identifier}"
        else:
            message = "Student not found"
        super().__init__(message)


class StudentProfileNotFoundError(StudentError):
    """Raised when a student profile is not found."""

    def __init__(self, identifier: str | int | None = None):
        self.identifier = identifier
        if identifier:
            message = f"Student profile not found: {identifier}"
        else:
            message = "Student profile not found"
        super().__init__(message)


class InvalidStudentDataError(StudentError):
    """Raised when student data validation fails."""

    def __init__(self, field: str | None = None, reason: str | None = None):
        self.field = field
        self.reason = reason
        if field and reason:
            message = f"Invalid student data for '{field}': {reason}"
        elif field:
            message = f"Invalid student data for '{field}'"
        elif reason:
            message = f"Invalid student data: {reason}"
        else:
            message = "Invalid student data"
        super().__init__(message)
