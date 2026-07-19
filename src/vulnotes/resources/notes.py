"""Notes attached to reports. Permissions: ``ro:reports`` / ``rw:reports``."""

from __future__ import annotations

from typing import Any

from .._utils import omit_none
from ._base import JSON, Resource


class Notes(Resource):
    def list_for_report(self, report_id: str) -> list[dict[str, Any]]:
        """Get all notes attached to a report."""
        return self._client.get(f"/notes/report/{report_id}")

    def create(
        self,
        report_id: str,
        title: str,
        *,
        content: str | None = None,
        is_pinned: bool | None = None,
        tags: list[str] | None = None,
    ) -> dict[str, Any]:
        """Create a note on a report. Requires ``rw:reports``."""
        body = omit_none(
            {"title": title, "content": content, "isPinned": is_pinned, "tags": tags}
        )
        return self._client.post(f"/notes/report/{report_id}", json=body)

    def get(self, note_id: str) -> dict[str, Any]:
        return self._client.get(f"/notes/{note_id}")

    def update(
        self,
        note_id: str,
        *,
        title: str | None = None,
        content: str | None = None,
        is_pinned: bool | None = None,
        tags: list[str] | None = None,
    ) -> dict[str, Any]:
        """Update a note. Only the supplied fields are changed."""
        body = omit_none(
            {"title": title, "content": content, "isPinned": is_pinned, "tags": tags}
        )
        return self._client.put(f"/notes/{note_id}", json=body)

    def delete(self, note_id: str) -> JSON:
        return self._client.delete(f"/notes/{note_id}")

    def save(
        self,
        note_id: str,
        *,
        content: str | None = None,
        title: str | None = None,
    ) -> dict[str, Any]:
        """Autosave-style update of a note's content and title.

        Warning: this endpoint always rewrites the title. When ``title`` is
        omitted it is re-extracted from the first ``# heading`` line of the
        content, falling back to ``"Untitled Note"``. Pass ``title``
        explicitly (or use :meth:`update`) to keep the existing one.
        """
        body = omit_none({"content": content, "title": title})
        return self._client.patch(f"/notes/{note_id}/save", json=body)

    def toggle_pin(self, note_id: str) -> dict[str, Any]:
        """Toggle the note's pinned status."""
        return self._client.patch(f"/notes/{note_id}/toggle-pin")
