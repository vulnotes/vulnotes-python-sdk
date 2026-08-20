"""Report template lifecycle. Permissions: ``ro:templates`` / ``rw:templates``."""

from __future__ import annotations

import builtins
from collections.abc import Iterator
from typing import Any

from .._utils import FileTypes, omit_none, prepare_file
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

    def import_docx(
        self,
        file: FileTypes,
        *,
        language: str = "en",
        timeout: float | None = 120.0,
    ) -> dict[str, Any]:
        """Convert a DOCX file into an unsaved template draft."""
        prepared = prepare_file(file, default_name="template.docx")
        try:
            if not str(prepared[0]).lower().endswith(".docx"):
                raise ValueError("template import requires a .docx filename")
            return self._client.post(
                "/templates/import/docx",
                data={"language": language},
                files={"file": prepared},
                timeout=timeout,
            )
        finally:
            fh = prepared[1]
            if hasattr(fh, "close"):
                fh.close()

    def create(
        self,
        name: str,
        *,
        language: str | None = None,
        html_content: dict[str, Any] | None = None,
        builder_state: Any | None = None,
        variables: builtins.list[dict[str, Any]] | None = None,
        category_order: builtins.list[str] | None = None,
        vulnerability_template: str | None = None,
        vulnerability_templates: builtins.list[str] | None = None,
    ) -> dict[str, Any]:
        """Create a report template. Requires ``rw:templates``."""
        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty string")
        body = omit_none(
            {
                "name": name,
                "language": language,
                "htmlContent": html_content,
                "builderState": builder_state,
                "variables": variables,
                "categoryOrder": category_order,
                "vulnerabilityTemplate": vulnerability_template,
                "vulnerabilityTemplates": vulnerability_templates,
            }
        )
        return self._client.post("/templates", json=body)

    def update(
        self,
        template_id: str,
        *,
        name: str | None = None,
        language: str | None = None,
        is_public: bool | None = None,
        variables: builtins.list[dict[str, Any]] | None = None,
        category_order: builtins.list[str] | None = None,
        vulnerability_template: str | None = None,
        vulnerability_templates: builtins.list[str] | None = None,
    ) -> dict[str, Any]:
        """Update template metadata and vulnerability-template associations."""
        body = omit_none(
            {
                "name": name,
                "language": language,
                "isPublic": is_public,
                "variables": variables,
                "categoryOrder": category_order,
                "vulnerabilityTemplate": vulnerability_template,
                "vulnerabilityTemplates": vulnerability_templates,
            }
        )
        return self._client.put(f"/templates/{template_id}", json=body)

    def clone(self, template_id: str, *, name: str | None = None) -> dict[str, Any]:
        """Create an independent copy of a template."""
        return self._client.post(
            f"/templates/{template_id}/clone", json=omit_none({"name": name})
        )

    def translate(
        self, template_id: str, language: str, *, name: str | None = None
    ) -> dict[str, Any]:
        """Create a language sibling in the source template's translation group."""
        if not isinstance(language, str) or not language.strip():
            raise ValueError("language must be a non-empty string")
        return self._client.post(
            f"/templates/{template_id}/translate",
            json=omit_none({"language": language, "name": name}),
        )

    def save_content(
        self,
        template_id: str,
        html_pages: builtins.list[Any],
        *,
        global_styles: str | None = None,
        builder_state: Any | None = None,
        variables: builtins.list[dict[str, Any]] | None = None,
        category_order: builtins.list[str] | None = None,
        findings_ai_context: Any | None = None,
    ) -> dict[str, Any]:
        """Save builder content and create a deduplicated template revision."""
        if not isinstance(html_pages, list):
            raise TypeError("html_pages must be a list")
        body = omit_none(
            {
                "htmlPages": html_pages,
                "globalStyles": global_styles,
                "builderState": builder_state,
                "variables": variables,
                "categoryOrder": category_order,
                "findingsAiContext": findings_ai_context,
            }
        )
        return self._client.put(f"/templates/{template_id}/content", json=body)

    def clear_content(self, template_id: str) -> JSON:
        """Clear a template's saved builder content."""
        return self._client.delete(f"/templates/{template_id}/content")

    def delete(self, template_id: str) -> JSON:
        return self._client.delete(f"/templates/{template_id}")
