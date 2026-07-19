"""Report templates (read-only surface). Permission: ``ro:templates``."""

from __future__ import annotations

import builtins
from collections.abc import Iterator
from typing import Any

from .._utils import omit_none
from ._base import JSON, Resource, page_params, paginate


class ReportTemplates(Resource):
    def list(self, *, page: int | None = None, limit: int | None = None) -> JSON:
        """List report templates (plain list, or paginated envelope with ``page``/``limit``)."""
        return self._client.get("/templates", params=page_params(page, limit))

    def iter(self, *, limit: int = 100) -> Iterator[dict[str, Any]]:
        """Iterate over every report template, fetching pages lazily."""
        return paginate(lambda page, limit: self.list(page=page, limit=limit), limit=limit)

    def search(self, query: str) -> builtins.list[dict[str, Any]]:
        return self._client.get("/templates/search", params={"query": query})

    def get(self, template_id: str) -> dict[str, Any]:
        return self._client.get(f"/templates/{template_id}")

    def content(self, template_id: str) -> dict[str, Any]:
        """Get the template's HTML content."""
        return self._client.get(f"/templates/{template_id}/content")

    def revisions(self, template_id: str) -> builtins.list[dict[str, Any]]:
        """List the template's content revisions."""
        resp = self._client.get(f"/templates/{template_id}/revisions")
        if isinstance(resp, dict):
            return resp.get("revisions", [])
        return resp

    def revision(self, template_id: str, revision_id: str) -> dict[str, Any]:
        """Get a single content revision."""
        return self._client.get(f"/templates/{template_id}/revisions/{revision_id}")

    def preview(
        self,
        template_id: str,
        *,
        report_id: str | None = None,
        snapshot_id: str | None = None,
    ) -> dict[str, Any]:
        """Preview the template rendered with a report's (or snapshot's) data."""
        params = omit_none({"reportId": report_id, "snapshotId": snapshot_id})
        return self._client.get(f"/templates/{template_id}/preview", params=params)
