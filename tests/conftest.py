import json as jsonlib
from urllib.parse import parse_qs, urlsplit

import pytest
import requests
from requests.adapters import BaseAdapter

from vulnotes import VulnotesClient


class FakeAdapter(BaseAdapter):
    """A requests transport adapter that records requests and replays canned
    responses, so tests run fully offline."""

    def __init__(self):
        super().__init__()
        self.calls = []
        self._queue = []

    def queue(self, status=200, json=None, content=b"", headers=None):
        if json is not None:
            content = jsonlib.dumps(json).encode()
            headers = {"Content-Type": "application/json", **(headers or {})}
        self._queue.append((status, content, headers or {}))

    def send(self, request, **kwargs):
        self.calls.append(request)
        if self._queue:
            status, content, headers = self._queue.pop(0)
        else:
            status, content, headers = 200, b"null", {"Content-Type": "application/json"}
        resp = requests.Response()
        resp.status_code = status
        resp.headers.update(headers)
        resp._content = content
        resp.url = request.url
        resp.request = request
        resp.reason = requests.status_codes._codes.get(status, ["?"])[0]
        return resp

    def close(self):
        pass

    # ── assertion helpers ────────────────────────────────────────────────

    @property
    def last(self):
        return self.calls[-1]

    def last_json(self):
        return jsonlib.loads(self.last.body)

    def last_path(self):
        return urlsplit(self.last.url).path

    def last_query(self):
        return parse_qs(urlsplit(self.last.url).query)


@pytest.fixture
def fake():
    return FakeAdapter()


@pytest.fixture
def client(fake):
    c = VulnotesClient("https://acme.vulnotes.app", api_key="test-key", max_retries=0)
    c._session.mount("https://", fake)
    c._session.mount("http://", fake)
    yield c
    c.close()
