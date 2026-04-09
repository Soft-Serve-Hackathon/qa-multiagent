"""Domain exceptions — business rule violations and error types."""


class DomainError(Exception):
    """Base domain exception."""
    pass


class PromptInjectionDetected(DomainError):
    """Raised when prompt injection patterns are found in user input."""
    pass


class InvalidEmailError(DomainError):
    pass


class UnsupportedFileTypeError(DomainError):
    pass


class FileTooLargeError(DomainError):
    pass


class EmptyOrCorruptAttachmentError(DomainError):
    pass


class IncidentNotFoundError(DomainError):
    pass


class TriageFailedError(DomainError):
    pass


class TicketCreationFailedError(DomainError):
    pass


class NotificationFailedError(DomainError):
    pass
