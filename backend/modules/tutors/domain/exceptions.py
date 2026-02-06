"""
Domain exceptions for the tutors module.

These exceptions represent domain-level errors that can occur during
tutor-related operations. They are independent of infrastructure concerns.
"""


class TutorError(Exception):
    """Base exception for all tutor-related domain errors."""

    def __init__(self, message: str = "A tutor error occurred") -> None:
        self.message = message
        super().__init__(self.message)


class TutorNotFoundError(TutorError):
    """Raised when a tutor cannot be found."""

    def __init__(
        self,
        tutor_id: int | None = None,
        user_id: int | None = None,
    ) -> None:
        if tutor_id:
            message = f"Tutor with ID {tutor_id} not found"
        elif user_id:
            message = f"Tutor profile for user {user_id} not found"
        else:
            message = "Tutor not found"
        super().__init__(message)
        self.tutor_id = tutor_id
        self.user_id = user_id


class StudentNoteNotFoundError(TutorError):
    """Raised when a student note cannot be found."""

    def __init__(
        self,
        note_id: int | None = None,
        tutor_id: int | None = None,
        student_id: int | None = None,
    ) -> None:
        if note_id:
            message = f"Student note with ID {note_id} not found"
        elif tutor_id and student_id:
            message = f"Student note for tutor {tutor_id} and student {student_id} not found"
        elif tutor_id:
            message = f"No student notes found for tutor {tutor_id}"
        elif student_id:
            message = f"No student notes found for student {student_id}"
        else:
            message = "Student note not found"
        super().__init__(message)
        self.note_id = note_id
        self.tutor_id = tutor_id
        self.student_id = student_id


class AvailabilityConflictError(TutorError):
    """Raised when availability slots conflict with each other."""

    def __init__(
        self,
        day_of_week: int | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
        conflicting_start: str | None = None,
        conflicting_end: str | None = None,
    ) -> None:
        if day_of_week is not None and start_time and end_time:
            if conflicting_start and conflicting_end:
                message = (
                    f"Availability {start_time}-{end_time} on day {day_of_week} "
                    f"conflicts with existing availability {conflicting_start}-{conflicting_end}"
                )
            else:
                message = (
                    f"Availability {start_time}-{end_time} on day {day_of_week} "
                    f"conflicts with existing availability"
                )
        else:
            message = "Availability conflict detected"
        super().__init__(message)
        self.day_of_week = day_of_week
        self.start_time = start_time
        self.end_time = end_time
        self.conflicting_start = conflicting_start
        self.conflicting_end = conflicting_end


class VideoSettingsError(TutorError):
    """Raised when there is an error with video meeting settings."""

    def __init__(
        self,
        provider: str | None = None,
        reason: str | None = None,
    ) -> None:
        if provider and reason:
            message = f"Video settings error for provider '{provider}': {reason}"
        elif provider:
            message = f"Video settings error for provider '{provider}'"
        elif reason:
            message = f"Video settings error: {reason}"
        else:
            message = "Video settings error"
        super().__init__(message)
        self.provider = provider
        self.reason = reason


class InvalidAvailabilityError(TutorError):
    """Raised when availability data is invalid."""

    def __init__(
        self,
        reason: str | None = None,
        day_of_week: int | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
    ) -> None:
        if reason:
            message = f"Invalid availability: {reason}"
        elif start_time and end_time:
            message = f"Invalid availability: start time {start_time} must be before end time {end_time}"
        elif day_of_week is not None:
            message = f"Invalid availability for day {day_of_week}"
        else:
            message = "Invalid availability configuration"
        super().__init__(message)
        self.reason = reason
        self.day_of_week = day_of_week
        self.start_time = start_time
        self.end_time = end_time
