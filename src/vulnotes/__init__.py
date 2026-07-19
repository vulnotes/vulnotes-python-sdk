"""Official Python SDK for the Vulnotes API.

Usage:
    >>> from vulnotes import VulnotesClient
    >>> client = VulnotesClient("https://acme.vulnotes.app", api_key="...")
    >>> report = client.reports.create("External pentest Q3")
    >>> client.findings.add(report["_id"], {"title": "Open SSH port"})
"""

from ._version import __version__
from .client import VulnotesClient
from .exceptions import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError,
    ConflictError,
    NotFoundError,
    PermissionDeniedError,
    RateLimitError,
    ServerError,
    UnprocessableEntityError,
    VulnotesError,
)

__all__ = [
    "__version__",
    "VulnotesClient",
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
