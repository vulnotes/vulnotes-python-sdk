"""Findings embedded in a report. Permissions: ``ro:reports`` / ``rw:reports``."""

from __future__ import annotations

import builtins
from typing import Any

from ._base import JSON, Resource


class Findings(Resource):
    def list(self, report_id: str) -> builtins.list[dict[str, Any]]:
        """Get all findings for a report."""
        return self._client.get(f"/reports/{report_id}/findings")

    def add(self, report_id: str, finding: dict[str, Any]) -> dict[str, Any]:
        """Append a finding to a report. Requires ``rw:reports``.

        A unique ``id`` is generated automatically. If the report has a
        vulnerability template and ``fields`` is not provided, the field
        definitions are copied from it, and multilingual ``data`` entries are
        initialized for all supported languages.

        Example:
            >>> client.findings.add(report_id, {
            ...     "title": "SQL Injection in /login",
            ...     "severity": "Critical",
            ...     "cvss": {"vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"},
            ...     "data": {"EN": {"title": "SQL Injection in /login",
            ...                     "description": "..."}},
            ... })
        """
        return self._client.post(f"/reports/{report_id}/findings", json=finding)

    def replace_all(
        self, report_id: str, findings: builtins.list[dict[str, Any]]
    ) -> builtins.list[dict[str, Any]]:
        """Replace the report's entire findings array (also used for reordering)."""
        return self._client.put(f"/reports/{report_id}/findings", json=findings)

    def update(
        self, report_id: str, finding_id: str, changes: dict[str, Any]
    ) -> dict[str, Any]:
        """Partially update a finding.

        Accepted fields: ``title``, ``severity``, ``status``, ``description``,
        ``impact``, ``remediation``, ``references``, ``cvss``, ``cwe``,
        ``affectedSystems``, ``evidence``, ``data``, ``order``, ``fields``,
        ``isComplete``. Other fields are ignored.

        Args:
            report_id: The report's ObjectId.
            finding_id: The finding's ``id`` field (a generated string, not an ObjectId).
            changes: The fields to change.
        """
        return self._client.put(
            f"/reports/{report_id}/findings/{finding_id}", json=changes
        )

    def delete(self, report_id: str, finding_id: str) -> JSON:
        """Remove a finding from the report."""
        return self._client.delete(f"/reports/{report_id}/findings/{finding_id}")
