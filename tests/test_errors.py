import pytest

from vulnotes import (
    APIStatusError,
    AuthenticationError,
    BadRequestError,
    NotFoundError,
    PermissionDeniedError,
    RateLimitError,
    ServerError,
    VulnotesError,
)


@pytest.mark.parametrize(
    "status,exc",
    [
        (400, BadRequestError),
        (401, AuthenticationError),
        (403, PermissionDeniedError),
        (404, NotFoundError),
        (429, RateLimitError),
        (500, ServerError),
        (502, ServerError),
    ],
)
def test_status_mapping(client, fake, status, exc):
    fake.queue(status, json={"message": "nope"})
    with pytest.raises(exc) as ei:
        client.reports.get("x")
    assert ei.value.status_code == status
    assert ei.value.message == "nope"
    assert isinstance(ei.value, VulnotesError)


def test_message_from_error_key(client, fake):
    fake.queue(400, json={"error": "bad input"})
    with pytest.raises(BadRequestError, match="bad input"):
        client.reports.get("x")


def test_body_preserved(client, fake):
    body = {"message": "Validation error", "error": "title is required"}
    fake.queue(400, json=body)
    with pytest.raises(BadRequestError) as ei:
        client.reports.create("")
    assert ei.value.body == body


def test_non_json_error_body(client, fake):
    fake.queue(503, content=b"Service Unavailable", headers={"Content-Type": "text/plain"})
    with pytest.raises(ServerError) as ei:
        client.reports.get("x")
    assert "Service Unavailable" in str(ei.value)
    assert ei.value.body is None


def test_unmapped_4xx_uses_base_status_error(client, fake):
    fake.queue(418, json={"message": "teapot"})
    with pytest.raises(APIStatusError) as ei:
        client.reports.get("x")
    assert type(ei.value) is APIStatusError
