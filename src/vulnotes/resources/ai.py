"""AI-assisted features. Permissions: ``rw:vulnerabilities`` or ``rw:reports``
depending on the endpoint (noted per method)."""

from __future__ import annotations

import json
from collections.abc import Sequence
from typing import Any

from .._utils import FileTypes, omit_none, prepare_file
from ._base import Resource


class AI(Resource):
    def generate_vulnerability(
        self,
        request_description: str,
        category: str,
        language: str,
        fields: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Generate vulnerability content from a description. Requires ``rw:vulnerabilities``."""
        return self._client.post(
            "/ai/vulnerability/new",
            json={
                "request_description": request_description,
                "category": category,
                "language": language,
                "fields": fields,
            },
        )

    def translate_vulnerability(self, message: dict[str, Any]) -> dict[str, Any]:
        """Translate vulnerability content. Requires ``rw:vulnerabilities``."""
        return self._client.post("/ai/vulnerability/translate", json={"message": message})

    def generate_report_content(
        self,
        report_id: str,
        variable_key: str,
        *,
        user_prompt: str | None = None,
        vuln_template_id: str | None = None,
    ) -> dict[str, Any]:
        """Generate content for a report variable. Requires ``rw:reports``."""
        body = omit_none(
            {
                "variableKey": variable_key,
                "userPrompt": user_prompt,
                "vulnTemplateId": vuln_template_id,
            }
        )
        return self._client.post(f"/ai/report/{report_id}/generate-content", json=body)

    def improve_report_content(
        self,
        report_id: str,
        existing_content: str,
        *,
        variable_key: str | None = None,
        improvement_type: str | None = None,
    ) -> dict[str, Any]:
        """Improve existing report content. Requires ``rw:reports``."""
        body = omit_none(
            {
                "existingContent": existing_content,
                "variableKey": variable_key,
                "improvementType": improvement_type,
            }
        )
        return self._client.post(f"/ai/report/{report_id}/improve-content", json=body)

    def generate_finding_from_images(
        self,
        report_id: str,
        images: Sequence[FileTypes] = (),
        *,
        description: str | None = None,
        redacted_images: str | Sequence[dict[str, str]] | None = None,
        vuln_template_id: str | None = None,
        timeout: float | None = 300.0,
    ) -> dict[str, Any]:
        """Generate a finding from screenshot evidence. Requires ``rw:reports``.

        Args:
            images: Zero to five screenshots (paths, bytes, file objects, or
                ``(filename, fileobj)`` tuples). A non-empty ``description``
                is required when no image is supplied.
            description: Extra context for the generation.
            redacted_images: Redaction metadata as expected by the API.
            vuln_template_id: Vulnerability template guiding the output fields.
        """
        if len(images) > 5:
            raise ValueError("at most five images may be supplied")
        if not images and not (description and description.strip()):
            raise ValueError("description is required when no images are supplied")
        redacted_payload = redacted_images
        if redacted_images is not None and not isinstance(redacted_images, str):
            redacted_payload = json.dumps(list(redacted_images))
        data = omit_none(
            {
                "description": description,
                "redactedImages": redacted_payload,
                "vulnTemplateId": vuln_template_id,
            }
        )
        prepared = [prepare_file(img, default_name="image.png") for img in images]
        try:
            files = [("images", p) for p in prepared]
            return self._client.post(
                f"/ai/report/{report_id}/generate-finding",
                data=data,
                files=files,
                timeout=timeout,
            )
        finally:
            for p in prepared:
                if hasattr(p[1], "close"):
                    p[1].close()
