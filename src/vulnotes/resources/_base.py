"""Shared plumbing for resource namespaces."""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from ..client import VulnotesClient

# The API returns list endpoints in two shapes: a plain JSON array when no
# pagination parameters are supplied, or a paginated envelope
# {"success": true, "data": [...], "pagination": {"page", "limit", "total",
# "totalPages", "hasNextPage", ...}} when `page` or `limit` is present.
JSON = Any


class Resource:
    def __init__(self, client: VulnotesClient) -> None:
        self._client = client


def paginate(
    fetch: Callable[..., JSON],
    *,
    limit: int = 100,
    **kwargs: Any,
) -> Iterator[dict[str, Any]]:
    """Iterate every item of a paginated list endpoint, fetching pages lazily.

    ``fetch`` must accept ``page`` and ``limit`` keyword arguments and return
    either a plain list or a paginated envelope.
    """
    page = 1
    while True:
        result = fetch(page=page, limit=limit, **kwargs)
        if isinstance(result, list):
            # Server ignored pagination and returned everything at once.
            yield from result
            return
        items: list[dict[str, Any]] = result.get("data") or []
        yield from items
        if not items:
            return
        # Pagination metadata lives under "pagination"; fall back to
        # top-level keys for endpoints using the older flat envelope.
        meta = result.get("pagination")
        if not isinstance(meta, dict):
            meta = result
        has_next = meta.get("hasNextPage")
        if has_next is not None:
            if not has_next:
                return
        else:
            total_pages: int | None = meta.get("totalPages")
            if total_pages is None or page >= total_pages:
                return
        page += 1


def page_params(page: int | None, limit: int | None) -> dict[str, Any]:
    params: dict[str, Any] = {}
    if page is not None:
        params["page"] = page
    if limit is not None:
        params["limit"] = limit
    return params
