"""The reusable vulnerability library.

Permissions: ``ro:vulnerabilities`` / ``rw:vulnerabilities``.
"""

from __future__ import annotations

import builtins
from collections.abc import Iterator
from typing import Any

from .._utils import omit_none
from ._base import JSON, Resource, page_params, paginate


class Vulnerabilities(Resource):
    def list(self, *, page: int | None = None, limit: int | None = None) -> JSON:
        """List vulnerabilities (plain list, or paginated envelope with ``page``/``limit``)."""
        return self._client.get("/vulnerabilities", params=page_params(page, limit))

    def iter(self, *, limit: int = 100) -> Iterator[dict[str, Any]]:
        """Iterate over every vulnerability in the library, fetching pages lazily."""
        return paginate(lambda page, limit: self.list(page=page, limit=limit), limit=limit)

    def search(self, query: str) -> builtins.list[dict[str, Any]]:
        """Search the vulnerability library (accent-insensitive)."""
        return self._client.get("/vulnerabilities/search", params={"query": query})

    def get(self, vulnerability_id: str) -> dict[str, Any]:
        return self._client.get(f"/vulnerabilities/{vulnerability_id}")

    def create(
        self,
        title: str,
        *,
        category: str | None = None,
        template_id: str | None = None,
        languages: builtins.list[str] | None = None,
        data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a library vulnerability. Requires ``rw:vulnerabilities``.

        Args:
            title: Vulnerability title.
            category: Free-form category.
            template_id: Vulnerability template this entry conforms to.
            languages: Language codes present in ``data``.
            data: Language-keyed field data, e.g. ``{"EN": {"title": ..., "description": ...}}``.
        """
        body = omit_none(
            {
                "title": title,
                "category": category,
                "templateId": template_id,
                "languages": languages,
                "data": data,
            }
        )
        return self._client.post("/vulnerabilities", json=body)

    def update(
        self,
        vulnerability_id: str,
        title: str,
        *,
        category: str | None = None,
        template_id: str | None = None,
        data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Update a library vulnerability (``title`` is required by the API)."""
        body = omit_none(
            {
                "title": title,
                "category": category,
                "templateId": template_id,
                "data": data,
            }
        )
        return self._client.put(f"/vulnerabilities/{vulnerability_id}", json=body)

    def delete(self, vulnerability_id: str) -> JSON:
        return self._client.delete(f"/vulnerabilities/{vulnerability_id}")
