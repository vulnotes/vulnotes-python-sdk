"""Image upload and management. Permissions: ``ro:reports`` / ``rw:reports``."""

from __future__ import annotations

import builtins
from typing import Any

from .._utils import FileTypes, omit_none, prepare_file
from ._base import JSON, Resource


class Images(Resource):
    def list(
        self,
        *,
        template_id: str | None = None,
        client_id: str | None = None,
        report_id: str | None = None,
    ) -> builtins.list[dict[str, Any]]:
        """List images, optionally filtered by template, client, or report."""
        params = omit_none(
            {"templateId": template_id, "clientId": client_id, "reportId": report_id}
        )
        return self._client.get("/images", params=params)

    def upload(
        self,
        image: FileTypes,
        *,
        template_id: str | None = None,
        client_id: str | None = None,
        report_id: str | None = None,
        note_id: str | None = None,
        vulnerability_id: str | None = None,
        company_id: str | None = None,
        user_id: str | None = None,
    ) -> dict[str, Any]:
        """Upload an image and associate it with an entity. Requires ``rw:reports``.

        Args:
            image: A filesystem path, raw bytes, an open binary file object,
                or a ``(filename, fileobj_or_bytes)`` tuple.
            template_id / client_id / report_id / note_id / vulnerability_id /
                company_id / user_id: Entity to associate the image with.
        """
        data = omit_none(
            {
                "templateId": template_id,
                "clientId": client_id,
                "reportId": report_id,
                "noteId": note_id,
                "vulnerabilityId": vulnerability_id,
                "companyId": company_id,
                "userId": user_id,
            }
        )
        prepared = prepare_file(image, default_name="image.png")
        try:
            return self._client.post(
                "/images/upload", data=data, files={"image": prepared}
            )
        finally:
            fh = prepared[1]
            if hasattr(fh, "close"):
                fh.close()

    def list_for_note(self, note_id: str) -> builtins.list[dict[str, Any]]:
        return self._client.get(f"/images/note/{note_id}")

    def list_for_template(self, template_id: str) -> builtins.list[dict[str, Any]]:
        return self._client.get(f"/images/template/{template_id}")

    def list_for_user(self, user_id: str) -> builtins.list[dict[str, Any]]:
        return self._client.get(f"/images/user/{user_id}")

    def associate_with_template(
        self, template_id: str, image_ids: builtins.list[str]
    ) -> JSON:
        """Associate previously uploaded images with a template."""
        return self._client.post(
            f"/images/template/{template_id}/associate", json={"imageIds": image_ids}
        )

    def delete(self, image_id: str) -> JSON:
        return self._client.delete(f"/images/{image_id}")
