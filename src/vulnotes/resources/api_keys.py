"""Introspection of the API key making the request."""

from __future__ import annotations

from typing import Any

from ._base import Resource


class APIKeys(Resource):
    def me(self) -> dict[str, Any]:
        """Describe the API key making the request: its name, owner, and the
        effective permissions it currently holds.

        Useful to discover at runtime which endpoints the key may call.
        """
        return self._client.get("/api-keys/me")
