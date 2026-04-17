from __future__ import annotations

from typing import Any


class AppError(Exception):
    """Base application error returned through the API."""

    def __init__(
        self,
        *,
        status_code: int,
        code: str,
        message: str,
        details: Any | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details


class BadRequestError(AppError):
    def __init__(self, message: str, details: Any | None = None) -> None:
        super().__init__(status_code=400, code="bad_request", message=message, details=details)


class UnauthorizedError(AppError):
    def __init__(self, message: str = "Authentication is required.") -> None:
        super().__init__(status_code=401, code="unauthorized", message=message)


class ForbiddenError(AppError):
    def __init__(self, message: str = "You do not have access to this resource.") -> None:
        super().__init__(status_code=403, code="forbidden", message=message)


class NotFoundError(AppError):
    def __init__(self, message: str = "Resource not found.") -> None:
        super().__init__(status_code=404, code="not_found", message=message)


class ConflictError(AppError):
    def __init__(self, message: str, details: Any | None = None) -> None:
        super().__init__(status_code=409, code="conflict", message=message, details=details)


class ExternalConfigurationError(AppError):
    def __init__(self, message: str, details: Any | None = None) -> None:
        super().__init__(
            status_code=409,
            code="external_service_not_configured",
            message=message,
            details=details,
        )


class ExternalServiceError(AppError):
    def __init__(self, message: str, details: Any | None = None) -> None:
        super().__init__(
            status_code=502,
            code="external_service_error",
            message=message,
            details=details,
        )

