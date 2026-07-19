"""Exception hierarchy for the Vulnotes SDK.

All exceptions raised by the SDK inherit from :class:`VulnotesError`, so a
single ``except vulnotes.VulnotesError`` catches everything.
"""

from __future__ import annotations

from typing import Any

__all__ = [
    "VulnotesError",
    "APIConnectionError",
    "APITimeoutError",
    "APIStatusError",
    "BadRequestError",
    "AuthenticationError",
    "PermissionDeniedError",
    "NotFoundError",
    "ConflictError",
    "UnprocessableEntityError",
    "RateLimitError",
    "ServerError",
]


class VulnotesError(Exception):
    """Base class for every error raised by this SDK."""


class APIConnectionError(VulnotesError):
    """The API could not be reached (DNS failure, refused connection, TLS error...)."""


class APITimeoutError(APIConnectionError):
    """The request timed out."""


class APIStatusError(VulnotesError):
    """The API returned a non-2xx HTTP status.

    Attributes:
        status_code: The HTTP status code.
        message: Human-readable error message extracted from the response body.
        body: The parsed JSON error body when available, otherwise ``None``.
        response: The underlying ``requests.Response`` object.
    """

    def __init__(
        self,
        status_code: int,
        message: str,
        *,
        body: Any | None = None,
        response: Any = None,
    ) -> None:
        self.status_code = status_code
        self.message = message
        self.body = body
        self.response = response
        super().__init__(f"[{status_code}] {message}")


class BadRequestError(APIStatusError):
    """400 - the request was malformed or failed validation."""


class AuthenticationError(APIStatusError):
    """401 - the API key is missing, invalid, revoked, or its owner is disabled."""


class PermissionDeniedError(APIStatusError):
    """403 - the API key lacks the permission required by this endpoint."""


class NotFoundError(APIStatusError):
    """404 - the resource does not exist or is not visible to the key's owner.

    Note: Vulnotes intentionally returns 404 (not 403) for reports outside the
    owner's visibility, so their existence is not disclosed.
    """


class ConflictError(APIStatusError):
    """409 - the request conflicts with the current state of the resource."""


class UnprocessableEntityError(APIStatusError):
    """422 - the request was well-formed but semantically invalid."""


class RateLimitError(APIStatusError):
    """429 - too many requests."""


class ServerError(APIStatusError):
    """5xx - the server failed to process the request."""


_STATUS_MAP = {
    400: BadRequestError,
    401: AuthenticationError,
    403: PermissionDeniedError,
    404: NotFoundError,
    409: ConflictError,
    422: UnprocessableEntityError,
    429: RateLimitError,
}


def error_for_status(
    status_code: int,
    message: str,
    *,
    body: Any | None = None,
    response: Any = None,
) -> APIStatusError:
    """Build the most specific :class:`APIStatusError` subclass for a status code."""
    cls = _STATUS_MAP.get(status_code)
    if cls is None:
        cls = ServerError if status_code >= 500 else APIStatusError
    return cls(status_code, message, body=body, response=response)
