"""Live integration tests: exercise the SDK against a real Vulnotes instance.

These are skipped unless both environment variables are set:

    VULNOTES_TEST_URL      e.g. http://localhost:5005
    VULNOTES_TEST_API_KEY  a key with rw:reports, rw:clients, rw:vulnerabilities,
                           rw:vulnerability_templates and (optionally) planning scopes

Everything created is prefixed "SDK-IT" and deleted afterwards. Do not point
this at a production instance.
"""

from __future__ import annotations

import datetime as dt
import os
import uuid

import pytest

from vulnotes import (
    AuthenticationError,
    NotFoundError,
    VulnotesClient,
    VulnotesError,
)

URL = os.environ.get("VULNOTES_TEST_URL")
KEY = os.environ.get("VULNOTES_TEST_API_KEY")

pytestmark = pytest.mark.skipif(
    not (URL and KEY),
    reason="set VULNOTES_TEST_URL and VULNOTES_TEST_API_KEY to run live tests",
)

RUN_ID = uuid.uuid4().hex[:8]
PREFIX = f"SDK-IT-{RUN_ID}"
BOGUS_ID = "0" * 24


@pytest.fixture(scope="module")
def client():
    with VulnotesClient(URL, api_key=KEY) as c:
        yield c


@pytest.fixture(scope="module")
def permissions(client):
    return set(client.api_keys.me()["permissions"])


@pytest.fixture(scope="module")
def company(client):
    company = client.companies.create(f"{PREFIX} Corp")
    yield company
    try:
        client.companies.delete(company["_id"])
    except VulnotesError:
        pass


@pytest.fixture(scope="module")
def report(client, company):
    report = client.reports.create(
        f"{PREFIX} report",
        company=company["_id"],
        language="EN",
        start_date=dt.date(2026, 7, 1),
        end_date=dt.date(2026, 7, 15),
    )
    yield report
    try:
        client.reports.delete(report["_id"])
    except VulnotesError:
        pass


# ── key introspection ─────────────────────────────────────────────────────


def test_me_reports_scope(permissions):
    assert "rw:reports" in permissions, "these tests need an rw:reports key"


# ── companies ─────────────────────────────────────────────────────────────


def test_company_lifecycle(client, company):
    assert company["name"] == f"{PREFIX} Corp"

    fetched = client.companies.get(company["_id"])
    assert fetched["_id"] == company["_id"]

    hits = client.companies.search(PREFIX)
    assert any(c["_id"] == company["_id"] for c in hits)

    updated = client.companies.update(company["_id"], name=f"{PREFIX} Corp 2")
    assert updated["name"] == f"{PREFIX} Corp 2"

    envelope = client.companies.list(page=1, limit=5)
    assert "data" in envelope and "pagination" in envelope
    assert len(envelope["data"]) <= 5
    assert envelope["pagination"]["page"] == 1


# ── vulnerability library ─────────────────────────────────────────────────


def test_vulnerability_lifecycle(client):
    vuln = client.vulnerabilities.create(
        f"{PREFIX} SQLi",
        category="Injection",
        languages=["EN"],
        data={"EN": {"title": f"{PREFIX} SQLi", "description": "test entry"}},
    )
    try:
        assert vuln["title"] == f"{PREFIX} SQLi"
        assert client.vulnerabilities.get(vuln["_id"])["_id"] == vuln["_id"]

        hits = client.vulnerabilities.search(PREFIX)
        assert any(v["_id"] == vuln["_id"] for v in hits)

        updated = client.vulnerabilities.update(
            vuln["_id"], f"{PREFIX} SQLi v2", category="Injection"
        )
        assert updated["title"] == f"{PREFIX} SQLi v2"
    finally:
        client.vulnerabilities.delete(vuln["_id"])
    with pytest.raises(NotFoundError):
        client.vulnerabilities.get(vuln["_id"])


def test_vulnerability_template_lifecycle(client):
    vt = client.vulnerability_templates.create(
        f"{PREFIX} template",
        ["EN"],
        [
            {
                "id": "description",
                "name": "description",
                "label": "Description",
                "type": "richtext",
                "order": 1,
            }
        ],
        description="integration test template",
    )
    try:
        assert vt["name"] == f"{PREFIX} template"
        got = client.vulnerability_templates.get(vt["_id"])
        assert got["supportedLanguages"] == ["EN"]

        hits = client.vulnerability_templates.search(PREFIX)
        assert any(t["_id"] == vt["_id"] for t in hits)

        all_templates = client.vulnerability_templates.list()
        assert any(t["_id"] == vt["_id"] for t in all_templates)

        updated = client.vulnerability_templates.update(
            vt["_id"],
            f"{PREFIX} template v2",
            ["EN"],
            got["fields"],
        )
        assert updated["name"] == f"{PREFIX} template v2"

        linked = client.vulnerability_templates.report_templates(vt["_id"])
        assert isinstance(linked, list)
    finally:
        client.vulnerability_templates.delete(vt["_id"])


# ── report templates (read-only) ──────────────────────────────────────────


def test_report_templates_readonly(client):
    templates = client.templates.list()
    assert isinstance(templates, list)
    if templates:
        t = client.templates.get(templates[0]["_id"])
        assert t["_id"] == templates[0]["_id"]
        content = client.templates.content(templates[0]["_id"])
        assert content is not None
        revisions = client.templates.revisions(templates[0]["_id"])
        assert isinstance(revisions, list)


# ── reports & findings ────────────────────────────────────────────────────


def test_report_crud_and_search(client, report, company):
    assert report["title"] == f"{PREFIX} report"

    fetched = client.reports.get(report["_id"])
    assert fetched["title"] == f"{PREFIX} report"

    scope = {
        "description": "external perimeter",
        "entries": [{"type": "ip", "name": "Office", "value": "203.0.113.0/24"}],
    }
    client.reports.update(report["_id"], scope=scope, title=f"{PREFIX} report & retest")
    refetched = client.reports.get(report["_id"])
    assert refetched["title"] == f"{PREFIX} report & retest"  # stored verbatim
    assert refetched["scope"]["entries"][0]["value"] == "203.0.113.0/24"

    hits = client.reports.search(PREFIX)
    assert any(r["_id"] == report["_id"] for r in hits)

    seen = {r["_id"] for r in client.reports.iter(limit=2)}
    assert report["_id"] in seen


def test_finding_lifecycle(client, report):
    finding = client.findings.add(
        report["_id"],
        {
            "title": f"{PREFIX} finding",
            "severity": "High",
            "affectedSystems": ["203.0.113.10"],
            "data": {"EN": {"title": f"{PREFIX} finding", "description": "evidence"}},
        },
    )
    assert finding["id"].startswith("finding-")

    updated = client.findings.update(report["_id"], finding["id"], {"severity": "Critical"})
    assert updated["severity"] == "Critical"

    listed = client.findings.list(report["_id"])
    assert any(f["id"] == finding["id"] for f in listed)

    replaced = client.findings.replace_all(report["_id"], listed)
    assert len(replaced) == len(listed)

    client.findings.delete(report["_id"], finding["id"])
    assert all(f["id"] != finding["id"] for f in client.findings.list(report["_id"]))


def test_notes_lifecycle(client, report):
    note = client.notes.create(report["_id"], f"{PREFIX} note", content="<p>hello</p>")
    note_id = note["_id"]
    try:
        assert client.notes.get(note_id)["title"] == f"{PREFIX} note"

        client.notes.update(note_id, title=f"{PREFIX} note v2")
        # save() rewrites the title, so it must be passed along
        client.notes.save(note_id, content="<p>autosaved</p>", title=f"{PREFIX} note v2")
        client.notes.toggle_pin(note_id)

        listed = client.notes.list_for_report(report["_id"])
        mine = next(n for n in listed if n["_id"] == note_id)
        assert mine["title"] == f"{PREFIX} note v2"
        assert mine.get("isPinned") is True
    finally:
        client.notes.delete(note_id)


# 1x1 transparent PNG
PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
    "0000000d4944415478da63fcffff3f030005fe02fea72d994400000000"
    "49454e44ae426082"
)


def test_image_upload_and_delete(client, report):
    uploaded = client.images.upload((f"{PREFIX}.png", PNG), report_id=report["_id"])
    image = uploaded.get("image", uploaded)
    image_id = image.get("_id") or image.get("id")
    assert image_id
    try:
        listed = client.images.list(report_id=report["_id"])
        assert any((i.get("_id") or i.get("id")) == image_id for i in listed)
    finally:
        client.images.delete(image_id)


def test_attachment_upload_and_delete(client, report):
    uploaded = client.attachments.upload(
        (f"{PREFIX}.txt", b"scanner output"), report_id=report["_id"]
    )
    attachment = uploaded.get("attachment", uploaded)
    attachment_id = attachment.get("_id") or attachment.get("id")
    assert attachment_id
    try:
        listed = client.attachments.list_for_report(report["_id"])
        assert any((a.get("_id") or a.get("id")) == attachment_id for a in listed)
    finally:
        client.attachments.delete(attachment_id)


def test_snapshots_and_comments(client, report):
    snapshot = client.snapshots.create(report["_id"])
    snapshot_id = snapshot.get("_id") or snapshot.get("snapshot", {}).get("_id")
    assert snapshot_id

    listed = client.snapshots.list(report["_id"])
    assert any(s["_id"] == snapshot_id for s in listed)

    active = client.snapshots.active(report["_id"])
    assert active

    assert client.snapshots.get(report["_id"], snapshot_id)["_id"] == snapshot_id
    assert client.snapshots.diff(report["_id"], snapshot_id) is not None

    comment = client.comments.create(report["_id"], snapshot_id, f"{PREFIX} looks wrong")
    comment_id = comment["_id"]
    try:
        listed = client.comments.list(report["_id"], snapshot_id)
        assert any(c["_id"] == comment_id for c in listed)

        counts = client.comments.counts(report["_id"], snapshot_id)
        assert counts is not None

        client.comments.update(report["_id"], comment_id, f"{PREFIX} fixed wording")
        resolved = client.comments.toggle_resolved(report["_id"], comment_id)
        assert resolved is not None
    finally:
        client.comments.delete(report["_id"], comment_id)


def test_export_json_roundtrip_shape(client, report):
    export = client.reports.export_json(report["_id"])
    assert export["exportType"] == "vulnotes-report"
    assert export["report"]["title"].startswith(PREFIX)
    assert "vulnerabilities" in export and "notes" in export


def test_export_xlsx_is_spreadsheet(client, report):
    content = client.reports.export_xlsx(report["_id"], finding_fields=["title", "severity"])
    assert isinstance(content, bytes)
    assert content[:2] == b"PK", "XLSX files are ZIP containers"


def test_export_docx_from_html(client, report, tmp_path):
    out = tmp_path / "report.docx"
    content = client.reports.export_docx(
        report["_id"],
        "<html><body><h1>Test</h1><p>hello</p></body></html>",
        path=out,
    )
    assert content[:2] == b"PK", "DOCX files are ZIP containers"
    assert out.read_bytes() == content


def test_export_zip(client, report):
    try:
        content = client.reports.export_zip(
            report["_id"],
            "<html><body>hi</body></html>",
            password="secret123",
        )
    except VulnotesError as e:
        pytest.skip(f"ZIP export unavailable here (needs the PDF renderer): {e}")
    assert content[:2] == b"PK"


def test_export_pdf_legacy(client, report):
    # Server-side rendering needs a report template assigned
    templates = client.templates.list()
    if not templates:
        pytest.skip("no report templates on this instance")
    client.reports.update(report["_id"], template=templates[0]["_id"])
    try:
        content = client.reports.export_pdf(report["_id"])
    except VulnotesError as e:
        pytest.skip(f"server-side PDF rendering unavailable here: {e}")
    assert content[:5] == b"%PDF-"


# ── planning ──────────────────────────────────────────────────────────────


def test_planning_lifecycle(client, permissions, company):
    if "rw:planning" not in permissions:
        pytest.skip("key lacks rw:planning")

    users = client.planning.users()
    assert users, "no planning users visible to this key"
    user_id = users[0]["_id"]

    event = client.planning.create_event(
        f"{PREFIX} engagement",
        dt.datetime(2036, 3, 2, 9, 0),
        dt.datetime(2036, 3, 6, 18, 0),
        [user_id],
        "pentest",
        client=company["_id"],
        color="#3B82F6",
    )
    event_id = event["_id"]
    try:
        assert client.planning.get_event(event_id)["title"] == f"{PREFIX} engagement"

        conflicts = client.planning.check_conflicts(user_id, "2036-03-03", "2036-03-04")
        assert conflicts["hasConflict"] is True
        assert any(e["_id"] == event_id for e in conflicts["events"])

        in_range = client.planning.events_in_range("2036-03-01", "2036-03-07")
        assert any(e["_id"] == event_id for e in in_range)

        calendar = client.planning.calendar("2036-03-01", "2036-03-07")
        assert calendar is not None

        updated = client.planning.update_event(event_id, status="in-progress")
        assert updated["status"] == "in-progress"
    finally:
        if "manage:planning" in permissions:
            client.planning.delete_event(event_id)

    availability = client.planning.create_availability(
        "vacation", dt.date(2036, 4, 6), dt.date(2036, 4, 10)
    )
    availability_id = availability["_id"]
    try:
        in_range = client.planning.availability_in_range("2036-04-01", "2036-04-30")
        assert any(a["_id"] == availability_id for a in in_range)
        client.planning.update_availability(availability_id, description="spring break")
    finally:
        client.planning.delete_availability(availability_id)


# ── error behaviour ───────────────────────────────────────────────────────


def test_not_found_maps_to_exception(client):
    with pytest.raises(NotFoundError):
        client.reports.get(BOGUS_ID)


def test_bad_api_key_raises_authentication_error():
    with VulnotesClient(URL, api_key="vuln_sk_invalid", max_retries=0) as bad:
        with pytest.raises(AuthenticationError):
            bad.reports.list()


def test_report_deleted_cleanup_verification(client, company):
    scratch = client.reports.create(f"{PREFIX} scratch")
    client.reports.delete(scratch["_id"])
    with pytest.raises(NotFoundError):
        client.reports.get(scratch["_id"])
