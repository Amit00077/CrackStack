from __future__ import annotations

from typing import Any, Dict, Optional


class AppException(Exception):
    def __init__(
        self,
        status_code: int,
        error: str,
        code: str,
        details: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
    ):
        self.status_code = status_code
        self.error = error
        self.code = code
        self.details = details
        self.extra = extra or {}
        super().__init__(self.error)

    def to_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "error": self.error,
            "code": self.code,
        }
        if self.details:
            result["details"] = self.details
        if self.extra:
            result["extra"] = self.extra
        return result


class NotFoundException(AppException):
    def __init__(self, entity: str = "Resource", details: Optional[str] = None):
        super().__init__(
            status_code=404,
            error="Not Found",
            code=f"{entity.upper()}_NOT_FOUND",
            details=details or f"{entity} not found",
        )


class ConflictException(AppException):
    def __init__(self, code: str = "CONFLICT", details: Optional[str] = None):
        super().__init__(
            status_code=409,
            error="Conflict",
            code=code,
            details=details,
        )


class UnauthorizedException(AppException):
    def __init__(self, code: str = "UNAUTHORIZED", details: Optional[str] = None):
        super().__init__(
            status_code=401,
            error="Unauthorized",
            code=code,
            details=details,
        )


class ForbiddenException(AppException):
    def __init__(self, code: str = "FORBIDDEN", details: Optional[str] = None):
        super().__init__(
            status_code=403,
            error="Forbidden",
            code=code,
            details=details,
        )
