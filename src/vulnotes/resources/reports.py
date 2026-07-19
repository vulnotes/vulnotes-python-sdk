"""Reports: lifecycle, search, import/export. Permissions: ``ro:reports`` / ``rw:reports``."""

from __future__ import annotations

import builtins
import datetime as _dt
import os
from collections.abc import Iterator
from typing import Any, Union

from .._utils import iso, omit_none, write_bytes
from ._base import JSON, Resource, page_params, paginate

DateLike = Union[str, _dt.date, _dt.datetime]


class Reports(Resource):
    def list(self, *, page: int | None = None, limit: int | None = None) -> JSON:
        """List reports (plain list, or paginated envelope with ``page``/``limit``).

        Visibility: if the key owner's team uses contributors-only report
        visibility, only reports they created, contribute to, or review are
        returned.
        """
        return self._client.get("/reports", params=page_params(page, limit))

    def iter(self, *, limit: int = 100) -> Iterator[dict[str, Any]]:
        """Iterate over every visible report, fetching pages lazily."""
        return paginate(lambda page, limit: self.list(page=page, limit=limit), limit=limit)

    def search(self, query: str) -> builtins.list[dict[str, Any]]:
        return self._client.get("/reports/search", params={"query": query})

    def get(self, report_id: str) -> dict[str, Any]:
        return self._client.get(f"/reports/{report_id}")

    def create(
        self,
        title: str,
        *,
        company: str | None = None,
        template: str | None = None,
        vuln_template: str | None = None,
        language: str | None = None,
        start_date: DateLike | None = None,
        end_date: DateLike | None = None,
        scope: Any | None = None,
        contributors: builtins.list[str] | None = None,
        contacts: builtins.list[dict[str, Any]] | None = None,
        planning_event_id: str | None = None,
    ) -> dict[str, Any]:
        """Create a report. Requires ``rw:reports``.

        Args:
            title: Report title (stored verbatim).
            company: Company ObjectId.
            template: Report template ObjectId.
            vuln_template: Vulnerability template ObjectId.
            language: Report language code, e.g. ``"EN"``.
            start_date / end_date: Engagement dates (str, date or datetime).
            scope: Engagement scope, shaped as ``{"description": str,
                "entries": [{"type": "ip"|"url"|"other", "name": str,
                "value": str}]}``.
            contributors: User ObjectIds.
            contacts: Contact objects.
            planning_event_id: Planning event to link the report to.
        """
        body = omit_none(
            {
                "title": title,
                "company": company,
                "template": template,
                "vulnTemplate": vuln_template,
                "language": language,
                "startDate": iso(start_date),
                "endDate": iso(end_date),
                "scope": scope,
                "contributors": contributors,
                "contacts": contacts,
                "planningEventId": planning_event_id,
            }
        )
        return self._client.post("/reports", json=body)

    def update(
        self,
        report_id: str,
        *,
        title: str | None = None,
        status: str | None = None,
        company: str | None = None,
        contacts: builtins.list[dict[str, Any]] | None = None,
        template: str | None = None,
        remove_template: bool | None = None,
        vulnerability_template: str | None = None,
        remove_vulnerability_template: bool | None = None,
        language: str | None = None,
        start_date: DateLike | None = None,
        end_date: DateLike | None = None,
        scope: Any | None = None,
        content: Any | None = None,
        contributors: builtins.list[str] | None = None,
        findings: builtins.list[dict[str, Any]] | None = None,
        archive_html: str | None = None,
    ) -> dict[str, Any]:
        """Update a report. Only the supplied fields are changed.

        Setting ``status="completed"`` archives a PDF of the report; pass
        ``archive_html`` to control the archived rendering.
        """
        body = omit_none(
            {
                "title": title,
                "status": status,
                "company": company,
                "contacts": contacts,
                "template": template,
                "removeTemplate": remove_template,
                "vulnerabilityTemplate": vulnerability_template,
                "removeVulnerabilityTemplate": remove_vulnerability_template,
                "language": language,
                "startDate": iso(start_date),
                "endDate": iso(end_date),
                "scope": scope,
                "content": content,
                "contributors": contributors,
                "findings": findings,
                "archiveHtml": archive_html,
            }
        )
        return self._client.put(f"/reports/{report_id}", json=body)

    def delete(self, report_id: str) -> JSON:
        return self._client.delete(f"/reports/{report_id}")

    def sync_from_template(self, template_id: str) -> JSON:
        """Re-sync every report built from the given template with its latest content."""
        return self._client.post(f"/reports/sync-from-template/{template_id}")

    # ── import / export ──────────────────────────────────────────────────

    def import_json(
        self,
        export: dict[str, Any],
        *,
        import_options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Import a report from a Vulnotes JSON export.

        Args:
            export: A dict as produced by :meth:`export_json`
                (``exportType`` and ``report`` are required).
            import_options: Optional import behaviour overrides; merged into
                the payload as ``importOptions``.
        """
        body = dict(export)
        if import_options is not None:
            body["importOptions"] = import_options
        return self._client.post("/reports/import", json=body)

    def export_json(self, report_id: str) -> dict[str, Any]:
        """Export the full report with all related data as a self-contained dict."""
        return self._client.get(f"/reports/{report_id}/export/json")

    def export_pdf(
        self,
        report_id: str,
        *,
        html: str | None = None,
        file_name: str | None = None,
        path: str | os.PathLike[str] | None = None,
        timeout: float | None = 300.0,
    ) -> bytes:
        """Export the report as a PDF and return the raw bytes.

        Without ``html`` this uses the legacy server-side rendering endpoint.
        Note that server-side rendering does not support every layout feature;
        for a pixel-perfect export pass pre-rendered ``html`` from the app's
        preview. Requires a valid, non-expired license.

        Args:
            html: Pre-rendered HTML to generate the PDF from.
            file_name: Download filename hint.
            path: If given, also write the PDF to this file.
            timeout: PDF generation can be slow; defaults to 300 seconds.
        """
        if html is not None:
            content = self._client.post(
                f"/reports/{report_id}/export/pdf",
                json=omit_none({"html": html, "fileName": file_name}),
                raw=True,
                timeout=timeout,
            )
        else:
            content = self._client.get(
                f"/reports/{report_id}/export/pdf", raw=True, timeout=timeout
            )
        if path is not None:
            write_bytes(content, path)
        return content

    def export_docx(
        self,
        report_id: str,
        html: str,
        *,
        header_html: str | None = None,
        footer_html: str | None = None,
        landscape_header_html: str | None = None,
        landscape_footer_html: str | None = None,
        first_header_html: str | None = None,
        file_name: str | None = None,
        options: dict[str, Any] | None = None,
        path: str | os.PathLike[str] | None = None,
        timeout: float | None = 300.0,
    ) -> bytes:
        """Export the report as DOCX from pre-rendered HTML; returns raw bytes."""
        body = omit_none(
            {
                "html": html,
                "headerHtml": header_html,
                "footerHtml": footer_html,
                "landscapeHeaderHtml": landscape_header_html,
                "landscapeFooterHtml": landscape_footer_html,
                "firstHeaderHtml": first_header_html,
                "fileName": file_name,
                "options": options,
            }
        )
        content = self._client.post(
            f"/reports/{report_id}/export/docx", json=body, raw=True, timeout=timeout
        )
        if path is not None:
            write_bytes(content, path)
        return content

    def export_xlsx(
        self,
        report_id: str,
        *,
        finding_fields: builtins.list[str] | None = None,
        content_sections: builtins.list[str] | None = None,
        path: str | os.PathLike[str] | None = None,
        timeout: float | None = 120.0,
    ) -> bytes:
        """Export the report's findings as an XLSX spreadsheet; returns raw bytes.

        The API requires at least one finding field or content section to be
        selected, e.g. ``finding_fields=["title", "severity"]``.
        """
        body = omit_none(
            {"findingFields": finding_fields, "contentSections": content_sections}
        )
        content = self._client.post(
            f"/reports/{report_id}/export/xlsx", json=body, raw=True, timeout=timeout
        )
        if path is not None:
            write_bytes(content, path)
        return content

    def export_zip(
        self,
        report_id: str,
        html: str,
        *,
        file_name: str | None = None,
        password: str | None = None,
        path: str | os.PathLike[str] | None = None,
        timeout: float | None = 300.0,
    ) -> bytes:
        """Export the report as a (optionally password-protected) ZIP archive."""
        body = omit_none({"html": html, "fileName": file_name, "password": password})
        content = self._client.post(
            f"/reports/{report_id}/export/zip", json=body, raw=True, timeout=timeout
        )
        if path is not None:
            write_bytes(content, path)
        return content

    def archived_pdf(
        self,
        report_id: str,
        *,
        path: str | os.PathLike[str] | None = None,
    ) -> bytes:
        """Download the PDF archived when the report was marked completed.

        Raises :class:`~vulnotes.exceptions.NotFoundError` if no archived PDF exists.
        """
        content = self._client.get(f"/reports/{report_id}/archive", raw=True)
        if path is not None:
            write_bytes(content, path)
        return content
