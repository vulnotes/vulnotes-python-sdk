"""Report snapshots (review states). Permissions: ``ro:reports`` / ``rw:reports``."""

from __future__ import annotations

import builtins
from typing import Any

from .._utils import omit_none
from ._base import Resource


class Snapshots(Resource):
    def list(self, report_id: str) -> builtins.list[dict[str, Any]]:
        """Get the snapshot history for a report."""
        return self._client.get(f"/reports/{report_id}/snapshots")

    def create(self, report_id: str) -> dict[str, Any]:
        """Create a manual snapshot of the report's current state."""
        return self._client.post(f"/reports/{report_id}/snapshots")

    def active(self, report_id: str) -> dict[str, Any]:
        """Get the report's active snapshot."""
        return self._client.get(f"/reports/{report_id}/snapshots/active")

    def get(self, report_id: str, snapshot_id: str) -> dict[str, Any]:
        return self._client.get(f"/reports/{report_id}/snapshots/{snapshot_id}")

    def diff(self, report_id: str, snapshot_id: str) -> dict[str, Any]:
        """Diff a snapshot against the current report state."""
        return self._client.get(f"/reports/{report_id}/snapshots/{snapshot_id}/diff")

    def preview_data(self, report_id: str, snapshot_id: str) -> dict[str, Any]:
        """Get the data needed to render a preview of the snapshot."""
        return self._client.get(
            f"/reports/{report_id}/snapshots/{snapshot_id}/preview-data"
        )

    def revert_change(
        self,
        report_id: str,
        snapshot_id: str,
        target: str,
        *,
        key: str | None = None,
        finding_id: str | None = None,
        field_key: str | None = None,
    ) -> dict[str, Any]:
        """Revert one diff entry to its snapshot value.

        ``target`` is one of ``title``, ``executiveSummary``, ``scope``,
        ``content``, ``section``, ``finding`` or ``finding-field``.
        """
        allowed = {
            "title",
            "executiveSummary",
            "scope",
            "content",
            "section",
            "finding",
            "finding-field",
        }
        if target not in allowed:
            raise ValueError(f"target must be one of {sorted(allowed)}")
        if target in {"content", "section"} and not key:
            raise ValueError(f"key is required for target {target!r}")
        if target in {"finding", "finding-field"} and not finding_id:
            raise ValueError(f"finding_id is required for target {target!r}")
        if target == "finding-field" and not field_key:
            raise ValueError("field_key is required for target 'finding-field'")
        body = omit_none(
            {
                "target": target,
                "key": key,
                "findingId": finding_id,
                "fieldKey": field_key,
            }
        )
        return self._client.post(
            f"/reports/{report_id}/snapshots/{snapshot_id}/revert", json=body
        )
