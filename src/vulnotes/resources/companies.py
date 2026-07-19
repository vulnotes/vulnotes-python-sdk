"""Client companies. Permissions: ``ro:clients`` / ``rw:clients``."""

from __future__ import annotations

import builtins
from collections.abc import Iterator
from typing import Any

from .._utils import omit_none
from ._base import JSON, Resource, page_params, paginate


class Companies(Resource):
    def list(self, *, page: int | None = None, limit: int | None = None) -> JSON:
        """List companies, sorted by creation date descending.

        Returns a plain list when called without arguments, or a paginated
        envelope (``data`` plus a ``pagination`` object with ``page``,
        ``limit``, ``total``, ``totalPages``, ``hasNextPage``) when ``page``
        or ``limit`` is given.
        """
        return self._client.get("/companies", params=page_params(page, limit))

    def iter(self, *, limit: int = 100) -> Iterator[dict[str, Any]]:
        """Iterate over every company, fetching pages lazily."""
        return paginate(lambda page, limit: self.list(page=page, limit=limit), limit=limit)

    def search(self, query: str) -> builtins.list[dict[str, Any]]:
        """Search companies by name (accent-insensitive)."""
        return self._client.get("/companies/search", params={"query": query})

    def get(self, company_id: str) -> dict[str, Any]:
        return self._client.get(f"/companies/{company_id}")

    def create(
        self,
        name: str,
        *,
        logo: str | None = None,
        contacts: builtins.list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Create a company. Requires ``rw:clients``."""
        body = omit_none({"name": name, "logo": logo, "contacts": contacts})
        return self._client.post("/companies", json=body)

    def update(
        self,
        company_id: str,
        *,
        name: str | None = None,
        logo: str | None = None,
        contacts: builtins.list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Update a company. Only the supplied fields are changed."""
        body = omit_none({"name": name, "logo": logo, "contacts": contacts})
        return self._client.put(f"/companies/{company_id}", json=body)

    def delete(self, company_id: str) -> JSON:
        return self._client.delete(f"/companies/{company_id}")

    def portal_access(self, company_id: str) -> dict[str, Any]:
        """Get the company's client-portal access configuration and users."""
        return self._client.get(f"/companies/{company_id}/portal-access")

    def update_client_user(
        self,
        company_id: str,
        user_id: str,
        *,
        client_role: str | None = None,
        active: bool | None = None,
    ) -> dict[str, Any]:
        """Update a company's client-portal user (role and/or active status)."""
        body = omit_none({"clientRole": client_role, "active": active})
        return self._client.patch(
            f"/companies/{company_id}/client-users/{user_id}", json=body
        )
