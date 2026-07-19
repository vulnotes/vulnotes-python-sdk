"""File attachments. Permissions: ``ro:reports`` / ``rw:reports``."""

from __future__ import annotations

import builtins
from typing import Any

from .._utils import FileTypes, omit_none, prepare_file
from ._base import JSON, Resource


class Attachments(Resource):
    def list(
        self,
        *,
        template_id: str | None = None,
        company_id: str | None = None,
        report_id: str | None = None,
        vulnerability_id: str | None = None,
        note_id: str | None = None,
    ) -> builtins.list[dict[str, Any]]:
        """List attachments, optionally filtered by associated entity."""
        params = omit_none(
            {
                "templateId": template_id,
                "companyId": company_id,
                "reportId": report_id,
                "vulnerabilityId": vulnerability_id,
                "noteId": note_id,
            }
        )
        return self._client.get("/attachments", params=params)

    def upload(
        self,
        file: FileTypes,
        *,
        template_id: str | None = None,
        company_id: str | None = None,
        report_id: str | None = None,
        vulnerability_id: str | None = None,
        note_id: str | None = None,
        user_id: str | None = None,
    ) -> dict[str, Any]:
        """Upload a file attachment. Requires ``rw:reports``.

        Args:
            file: A filesystem path, raw bytes, an open binary file object,
                or a ``(filename, fileobj_or_bytes)`` tuple.
        """
        data = omit_none(
            {
                "templateId": template_id,
                "companyId": company_id,
                "reportId": report_id,
                "vulnerabilityId": vulnerability_id,
                "noteId": note_id,
                "userId": user_id,
            }
        )
        prepared = prepare_file(file, default_name="attachment.bin")
        try:
            return self._client.post(
                "/attachments/upload", data=data, files={"file": prepared}
            )
        finally:
            fh = prepared[1]
            if hasattr(fh, "close"):
                fh.close()

    def list_for_report(self, report_id: str) -> builtins.list[dict[str, Any]]:
        return self._client.get(f"/attachments/report/{report_id}")

    def delete(self, attachment_id: str) -> JSON:
        return self._client.delete(f"/attachments/{attachment_id}")
