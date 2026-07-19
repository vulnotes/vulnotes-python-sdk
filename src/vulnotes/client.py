"""The Vulnotes API client."""

from __future__ import annotations

import os
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ._version import __version__
from .exceptions import (
    APIConnectionError,
    APITimeoutError,
    VulnotesError,
    error_for_status,
)
from .resources.ai import AI
from .resources.api_keys import APIKeys
from .resources.attachments import Attachments
from .resources.comments import Comments
from .resources.companies import Companies
from .resources.findings import Findings
from .resources.images import Images
from .resources.notes import Notes
from .resources.planning import Planning
from .resources.report_templates import ReportTemplates
from .resources.reports import Reports
from .resources.snapshots import Snapshots
from .resources.vulnerabilities import Vulnerabilities
from .resources.vulnerability_templates import VulnerabilityTemplates

__all__ = ["VulnotesClient"]

_RETRYABLE_METHODS = frozenset(["GET", "HEAD", "OPTIONS", "PUT", "DELETE"])


class VulnotesClient:
    """Client for the Vulnotes REST API.

    Authentication uses an API key (created in **Settings → API Keys** inside
    Vulnotes) sent via the ``X-API-Key`` header. The key carries an explicit
    set of permissions and can never exceed what its owner may do.

    Args:
        base_url: Root URL of your Vulnotes instance, e.g.
            ``https://acme.vulnotes.app``. A trailing ``/api`` is added
            automatically if not present. Falls back to the ``VULNOTES_URL``
            environment variable.
        api_key: Your API key. Falls back to the ``VULNOTES_API_KEY``
            environment variable.
        timeout: Default per-request timeout in seconds (connect + read).
        verify_ssl: Set to ``False`` to skip TLS certificate verification
            (only for lab instances with self-signed certificates).
        max_retries: Automatic retries for idempotent requests that fail with
            a connection error or a 429/502/503/504 status.
        session: Optionally supply a pre-configured ``requests.Session``.

    Example:
        >>> from vulnotes import VulnotesClient
        >>> client = VulnotesClient("https://acme.vulnotes.app", api_key="...")
        >>> for report in client.reports.iter():
        ...     print(report["title"])
    """

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        *,
        timeout: float = 30.0,
        verify_ssl: bool = True,
        max_retries: int = 3,
        session: requests.Session | None = None,
    ) -> None:
        base_url = base_url or os.environ.get("VULNOTES_URL")
        api_key = api_key or os.environ.get("VULNOTES_API_KEY")
        if not base_url:
            raise VulnotesError(
                "No base_url provided. Pass it to VulnotesClient(...) or set the "
                "VULNOTES_URL environment variable."
            )
        if not api_key:
            raise VulnotesError(
                "No api_key provided. Create one in Settings → API Keys, then pass "
                "it to VulnotesClient(...) or set the VULNOTES_API_KEY environment variable."
            )

        base_url = base_url.rstrip("/")
        if not base_url.endswith("/api"):
            base_url += "/api"
        self.base_url = base_url
        self.timeout = timeout

        self._session = session or requests.Session()
        self._session.verify = verify_ssl
        self._session.headers["X-API-Key"] = api_key
        self._session.headers["User-Agent"] = f"vulnotes-python/{__version__}"
        if max_retries:
            retry = Retry(
                total=max_retries,
                connect=max_retries,
                read=max_retries,
                status=max_retries,
                backoff_factor=0.5,
                status_forcelist=(429, 502, 503, 504),
                allowed_methods=_RETRYABLE_METHODS,
                raise_on_status=False,
            )
            adapter = HTTPAdapter(max_retries=retry)
            self._session.mount("https://", adapter)
            self._session.mount("http://", adapter)

        # Resource namespaces
        self.companies = Companies(self)
        self.templates = ReportTemplates(self)
        self.vulnerability_templates = VulnerabilityTemplates(self)
        self.vulnerabilities = Vulnerabilities(self)
        self.reports = Reports(self)
        self.findings = Findings(self)
        self.snapshots = Snapshots(self)
        self.comments = Comments(self)
        self.notes = Notes(self)
        self.images = Images(self)
        self.attachments = Attachments(self)
        self.ai = AI(self)
        self.planning = Planning(self)
        self.api_keys = APIKeys(self)

    # ── low-level request machinery ──────────────────────────────────────

    def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: Any = None,
        data: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
        raw: bool = False,
        timeout: float | None = None,
    ) -> Any:
        """Perform an HTTP request against the API.

        This is the escape hatch for endpoints not (yet) wrapped by a resource
        method: ``client.request("GET", "/reports")``.

        Returns the parsed JSON body, raw ``bytes`` when ``raw=True``, or
        ``None`` for empty responses. Some endpoints wrap their payload in a
        ``{"success": true, "data": ...}`` envelope; those are transparently
        unwrapped so every method returns the entity itself. Raises a subclass
        of :class:`~vulnotes.exceptions.VulnotesError` on failure.
        """
        url = self.base_url + (path if path.startswith("/") else "/" + path)
        try:
            resp = self._session.request(
                method,
                url,
                params=params,
                json=json,
                data=data,
                files=files,
                timeout=timeout if timeout is not None else self.timeout,
            )
        except requests.Timeout as exc:
            raise APITimeoutError(f"Request to {url} timed out") from exc
        except requests.RequestException as exc:
            raise APIConnectionError(f"Could not reach {url}: {exc}") from exc

        if not resp.ok:
            body: Any = None
            try:
                body = resp.json()
            except ValueError:
                pass
            if isinstance(body, dict):
                message = body.get("message") or body.get("error") or resp.text
            else:
                message = resp.text or resp.reason
            raise error_for_status(resp.status_code, str(message), body=body, response=resp)

        if raw:
            return resp.content
        if resp.status_code == 204 or not resp.content:
            return None
        content_type = resp.headers.get("Content-Type", "")
        if "application/json" in content_type:
            payload = resp.json()
            # Normalize the {"success": true, "data": ...} envelope some
            # endpoints use, so callers always get the entity itself.
            # Paginated envelopes carry a "pagination" key and stay intact.
            if (
                isinstance(payload, dict)
                and "data" in payload
                and set(payload) <= {"success", "data", "message"}
            ):
                return payload["data"]
            return payload
        return resp.content

    def get(self, path: str, **kwargs: Any) -> Any:
        return self.request("GET", path, **kwargs)

    def post(self, path: str, **kwargs: Any) -> Any:
        return self.request("POST", path, **kwargs)

    def put(self, path: str, **kwargs: Any) -> Any:
        return self.request("PUT", path, **kwargs)

    def patch(self, path: str, **kwargs: Any) -> Any:
        return self.request("PATCH", path, **kwargs)

    def delete(self, path: str, **kwargs: Any) -> Any:
        return self.request("DELETE", path, **kwargs)

    # ── lifecycle ────────────────────────────────────────────────────────

    def close(self) -> None:
        """Release the underlying HTTP connection pool."""
        self._session.close()

    def __enter__(self) -> VulnotesClient:
        return self

    def __exit__(self, *exc_info: Any) -> None:
        self.close()
