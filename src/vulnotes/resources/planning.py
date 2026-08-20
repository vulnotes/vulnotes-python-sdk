"""The resource-planning calendar: engagements and availability.

Permissions: ``ro:planning`` to read, ``rw:planning`` to write,
``manage:planning`` to delete events or assign users outside your own team.
"""

from __future__ import annotations

import datetime as _dt
import os
from collections.abc import Iterator
from typing import Any, Union

from .._utils import FileTypes, iso, omit_none, prepare_file, write_bytes
from ._base import JSON, Resource, page_params, paginate

DateLike = Union[str, _dt.date, _dt.datetime]


class Planning(Resource):
    # ── calendar ─────────────────────────────────────────────────────────

    def calendar(self, start: DateLike, end: DateLike) -> dict[str, Any]:
        """Get the combined planning calendar (events + availability) for a date range."""
        return self._client.get(
            "/planning/calendar", params={"start": iso(start), "end": iso(end)}
        )

    def users(self, *, skills: str | None = None) -> list[dict[str, Any]]:
        """List calendar users, optionally filtered by skills."""
        return self._client.get("/planning/users", params=omit_none({"skills": skills}))

    # ── events ───────────────────────────────────────────────────────────

    def list_events(
        self, *, page: int | None = None, limit: int | None = None
    ) -> JSON:
        """List planning events (plain list, or paginated envelope with ``page``/``limit``)."""
        return self._client.get("/planning/events", params=page_params(page, limit))

    def iter_events(self, *, limit: int = 100) -> Iterator[dict[str, Any]]:
        """Iterate over every visible planning event, fetching pages lazily."""
        return paginate(
            lambda page, limit: self.list_events(page=page, limit=limit), limit=limit
        )

    def events_in_range(self, start: DateLike, end: DateLike) -> list[dict[str, Any]]:
        """List planning events overlapping a date range."""
        return self._client.get(
            "/planning/events/range", params={"start": iso(start), "end": iso(end)}
        )

    def check_conflicts(
        self,
        user_id: str,
        start: DateLike,
        end: DateLike,
        *,
        exclude_event_id: str | None = None,
    ) -> dict[str, Any]:
        """Check whether a user is already booked during a date range."""
        params = omit_none(
            {"start": iso(start), "end": iso(end), "excludeEventId": exclude_event_id}
        )
        return self._client.get(f"/planning/events/conflicts/{user_id}", params=params)

    def get_event(self, event_id: str) -> dict[str, Any]:
        return self._client.get(f"/planning/events/{event_id}")

    def create_event(
        self,
        title: str,
        start_date: DateLike,
        end_date: DateLike,
        assignees: list[str],
        event_type: str,
        *,
        description: str | None = None,
        client: str | None = None,
        status: str | None = None,
        color: str | None = None,
        notes: str | None = None,
    ) -> dict[str, Any]:
        """Book an engagement on the calendar. Requires ``rw:planning``.

        Args:
            title: Event title (max 200 chars).
            start_date / end_date: ``end_date`` must be strictly after ``start_date``.
            assignees: User ObjectIds (at least one). Non-admin callers may only
                assign members of their own team.
            event_type: One of ``pentest``, ``training``, ``conference``,
                ``research``, ``other``.
            client: Company ObjectId.
            status: One of ``planned``, ``requirements``, ``in-progress``,
                ``completed``, ``cancelled``.
            color: Hex color, e.g. ``"#3B82F6"``.
        """
        body = omit_none(
            {
                "title": title,
                "startDate": iso(start_date),
                "endDate": iso(end_date),
                "assignees": assignees,
                "eventType": event_type,
                "description": description,
                "client": client,
                "status": status,
                "color": color,
                "notes": notes,
            }
        )
        return self._client.post("/planning/events", json=body)

    def update_event(
        self,
        event_id: str,
        *,
        title: str | None = None,
        start_date: DateLike | None = None,
        end_date: DateLike | None = None,
        assignees: list[str] | None = None,
        event_type: str | None = None,
        description: str | None = None,
        client: str | None = None,
        status: str | None = None,
        color: str | None = None,
        notes: str | None = None,
    ) -> dict[str, Any]:
        """Update a planning event. Only the supplied fields are changed."""
        body = omit_none(
            {
                "title": title,
                "startDate": iso(start_date),
                "endDate": iso(end_date),
                "assignees": assignees,
                "eventType": event_type,
                "description": description,
                "client": client,
                "status": status,
                "color": color,
                "notes": notes,
            }
        )
        return self._client.put(f"/planning/events/{event_id}", json=body)

    def delete_event(self, event_id: str) -> JSON:
        """Delete a planning event. Requires ``manage:planning``."""
        return self._client.delete(f"/planning/events/{event_id}")

    def upload_attachment(
        self, event_id: str, file: FileTypes
    ) -> dict[str, Any]:
        """Upload an attachment to an editable planning event."""
        prepared = prepare_file(file, default_name="attachment.bin")
        try:
            return self._client.post(
                f"/planning/events/{event_id}/attachments", files={"file": prepared}
            )
        finally:
            fh = prepared[1]
            if hasattr(fh, "close"):
                fh.close()

    def download_attachment(
        self,
        event_id: str,
        attachment_id: str,
        *,
        path: str | os.PathLike[str] | None = None,
    ) -> bytes:
        """Download an attachment from a visible planning event."""
        content = self._client.get(
            f"/planning/events/{event_id}/attachments/{attachment_id}/download",
            raw=True,
        )
        if path is not None:
            write_bytes(content, path)
        return content

    def delete_attachment(self, event_id: str, attachment_id: str) -> JSON:
        """Delete an attachment from an editable planning event."""
        return self._client.delete(
            f"/planning/events/{event_id}/attachments/{attachment_id}"
        )

    # ── availability ─────────────────────────────────────────────────────

    def list_availability(
        self, *, page: int | None = None, limit: int | None = None
    ) -> JSON:
        """List availability entries (plain list, or paginated envelope)."""
        return self._client.get("/planning/availability", params=page_params(page, limit))

    def availability_in_range(
        self, start: DateLike, end: DateLike
    ) -> list[dict[str, Any]]:
        """List availability entries overlapping a date range."""
        return self._client.get(
            "/planning/availability/range", params={"start": iso(start), "end": iso(end)}
        )

    def create_availability(
        self,
        type: str,
        start_date: DateLike,
        end_date: DateLike,
        *,
        description: str | None = None,
    ) -> dict[str, Any]:
        """Mark availability for the API key's owner. Requires ``rw:planning``.

        Args:
            type: One of ``vacation``, ``conference``, ``sick``, ``training``, ``other``.
            start_date / end_date: ``end_date`` must be strictly after ``start_date``.
        """
        body = omit_none(
            {
                "type": type,
                "startDate": iso(start_date),
                "endDate": iso(end_date),
                "description": description,
            }
        )
        return self._client.post("/planning/availability", json=body)

    def update_availability(
        self,
        availability_id: str,
        *,
        type: str | None = None,
        start_date: DateLike | None = None,
        end_date: DateLike | None = None,
        description: str | None = None,
    ) -> dict[str, Any]:
        """Update an availability entry. Only the supplied fields are changed."""
        body = omit_none(
            {
                "type": type,
                "startDate": iso(start_date),
                "endDate": iso(end_date),
                "description": description,
            }
        )
        return self._client.put(f"/planning/availability/{availability_id}", json=body)

    def delete_availability(self, availability_id: str) -> JSON:
        return self._client.delete(f"/planning/availability/{availability_id}")
