"""Report snapshots (review states). Permissions: ``ro:reports`` / ``rw:reports``."""

from __future__ import annotations

import builtins
from typing import Any

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
