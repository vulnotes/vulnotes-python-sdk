"""Review comment threads on report snapshots.

Permissions: ``ro:reports`` / ``rw:reports``.
"""

from __future__ import annotations

import builtins
from typing import Any

from .._utils import omit_none
from ._base import JSON, Resource


class Comments(Resource):
    def list(
        self,
        report_id: str,
        snapshot_id: str,
        *,
        resolved: bool | None = None,
        type: str | None = None,
        ref: str | None = None,
    ) -> builtins.list[dict[str, Any]]:
        """List comments on a snapshot, optionally filtered by resolved state,
        attachment type, or attachment ref.

        Returns the comment list; use :meth:`counts` for the aggregate counts.
        """
        params = omit_none(
            {
                "resolved": str(resolved).lower() if resolved is not None else None,
                "type": type,
                "ref": ref,
            }
        )
        resp = self._client.get(
            f"/reports/{report_id}/snapshots/{snapshot_id}/comments", params=params
        )
        if isinstance(resp, dict):
            return resp.get("comments", [])
        return resp

    def create(
        self,
        report_id: str,
        snapshot_id: str,
        content: str,
        *,
        attachment_type: str | None = None,
        attachment_ref: str | None = None,
        finding_field: str | None = None,
        parent_comment: str | None = None,
        page_number: int | None = None,
        bounding_box: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a review comment (or a reply, via ``parent_comment``)."""
        body = omit_none(
            {
                "content": content,
                "attachmentType": attachment_type,
                "attachmentRef": attachment_ref,
                "findingField": finding_field,
                "parentComment": parent_comment,
                "pageNumber": page_number,
                "boundingBox": bounding_box,
            }
        )
        return self._client.post(
            f"/reports/{report_id}/snapshots/{snapshot_id}/comments", json=body
        )

    def counts(self, report_id: str, snapshot_id: str) -> dict[str, Any]:
        """Get comment counts for a snapshot
        (``total`` / ``unresolved`` / ``resolved`` / ``byType``)."""
        return self._client.get(
            f"/reports/{report_id}/snapshots/{snapshot_id}/comments/counts"
        )

    def annotations(self, report_id: str, snapshot_id: str) -> JSON:
        """Get PDF annotations for a snapshot, as ``{"annotations": [...],
        "byPage": {...}}``."""
        return self._client.get(
            f"/reports/{report_id}/snapshots/{snapshot_id}/annotations"
        )

    def update(self, report_id: str, comment_id: str, content: str) -> dict[str, Any]:
        """Edit a comment's content."""
        return self._client.put(
            f"/reports/{report_id}/comments/{comment_id}", json={"content": content}
        )

    def delete(self, report_id: str, comment_id: str) -> JSON:
        return self._client.delete(f"/reports/{report_id}/comments/{comment_id}")

    def toggle_resolved(self, report_id: str, comment_id: str) -> dict[str, Any]:
        """Toggle a comment's resolved status."""
        return self._client.patch(f"/reports/{report_id}/comments/{comment_id}/resolve")
