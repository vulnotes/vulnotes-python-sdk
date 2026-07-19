import pytest

import vulnotes
from vulnotes import VulnotesClient, VulnotesError


def test_base_url_gets_api_suffix(client, fake):
    client.reports.list()
    assert fake.last.url == "https://acme.vulnotes.app/api/reports"


def test_base_url_api_suffix_not_doubled(fake):
    c = VulnotesClient("https://acme.vulnotes.app/api/", api_key="k", max_retries=0)
    c._session.mount("https://", fake)
    c.reports.list()
    assert fake.last.url == "https://acme.vulnotes.app/api/reports"


def test_api_key_header_and_user_agent(client, fake):
    client.api_keys.me()
    assert fake.last.headers["X-API-Key"] == "test-key"
    assert fake.last.headers["User-Agent"] == f"vulnotes-python/{vulnotes.__version__}"


def test_env_var_fallback(monkeypatch):
    monkeypatch.setenv("VULNOTES_URL", "https://env.vulnotes.app")
    monkeypatch.setenv("VULNOTES_API_KEY", "env-key")
    c = VulnotesClient()
    assert c.base_url == "https://env.vulnotes.app/api"
    assert c._session.headers["X-API-Key"] == "env-key"


def test_missing_configuration_raises(monkeypatch):
    monkeypatch.delenv("VULNOTES_URL", raising=False)
    monkeypatch.delenv("VULNOTES_API_KEY", raising=False)
    with pytest.raises(VulnotesError, match="base_url"):
        VulnotesClient()
    with pytest.raises(VulnotesError, match="api_key"):
        VulnotesClient("https://acme.vulnotes.app")


def test_context_manager_closes_session(fake):
    with VulnotesClient("https://a.b", api_key="k", max_retries=0) as c:
        c._session.mount("https://", fake)
        c.reports.list()
    # closed without error


def test_non_json_success_returns_bytes(client, fake):
    fake.queue(200, content=b"%PDF-1.7", headers={"Content-Type": "application/pdf"})
    result = client.request("GET", "/reports/x/archive")
    assert result == b"%PDF-1.7"


def test_empty_response_returns_none(client, fake):
    fake.queue(204)
    assert client.request("DELETE", "/notes/x") is None
