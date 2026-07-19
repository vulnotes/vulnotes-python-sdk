import datetime as dt
import io


def test_company_create_omits_none(client, fake):
    fake.queue(201, json={"_id": "c1", "name": "Acme"})
    client.companies.create("Acme")
    assert fake.last.method == "POST"
    assert fake.last_path() == "/api/companies"
    assert fake.last_json() == {"name": "Acme"}


def test_company_update_client_user(client, fake):
    fake.queue(200, json={})
    client.companies.update_client_user("c1", "u1", active=False)
    assert fake.last.method == "PATCH"
    assert fake.last_path() == "/api/companies/c1/client-users/u1"
    assert fake.last_json() == {"active": False}


def test_search_endpoints_use_query_param(client, fake):
    for resource, path in [
        (client.companies, "/api/companies/search"),
        (client.reports, "/api/reports/search"),
        (client.vulnerabilities, "/api/vulnerabilities/search"),
        (client.templates, "/api/templates/search"),
        (client.vulnerability_templates, "/api/vulnerability-templates/search"),
    ]:
        fake.queue(200, json=[])
        resource.search("sqli")
        assert fake.last_path() == path
        assert fake.last_query() == {"query": ["sqli"]}


def test_finding_crud_paths(client, fake):
    fake.queue(201, json={"id": "f1"})
    client.findings.add("r1", {"title": "XSS"})
    assert fake.last_path() == "/api/reports/r1/findings"
    assert fake.last_json() == {"title": "XSS"}

    fake.queue(200, json={"id": "f1"})
    client.findings.update("r1", "f1", {"severity": "High"})
    assert fake.last.method == "PUT"
    assert fake.last_path() == "/api/reports/r1/findings/f1"

    fake.queue(200, json=[{"id": "f1"}])
    client.findings.replace_all("r1", [{"id": "f1"}])
    assert fake.last_json() == [{"id": "f1"}]

    fake.queue(200, json={"message": "Finding deleted successfully"})
    client.findings.delete("r1", "f1")
    assert fake.last.method == "DELETE"


def test_report_create_maps_snake_case_and_dates(client, fake):
    fake.queue(201, json={"_id": "r1"})
    client.reports.create(
        "Q3 pentest",
        vuln_template="vt1",
        start_date=dt.date(2026, 7, 1),
        end_date="2026-07-15",
        planning_event_id="pe1",
    )
    assert fake.last_json() == {
        "title": "Q3 pentest",
        "vulnTemplate": "vt1",
        "startDate": "2026-07-01",
        "endDate": "2026-07-15",
        "planningEventId": "pe1",
    }


def test_export_pdf_legacy_get_returns_bytes(client, fake, tmp_path):
    fake.queue(200, content=b"%PDF-1.7 fake", headers={"Content-Type": "application/pdf"})
    out = tmp_path / "report.pdf"
    content = client.reports.export_pdf("r1", path=out)
    assert fake.last.method == "GET"
    assert fake.last_path() == "/api/reports/r1/export/pdf"
    assert content == b"%PDF-1.7 fake"
    assert out.read_bytes() == b"%PDF-1.7 fake"


def test_export_pdf_with_html_posts(client, fake):
    fake.queue(200, content=b"%PDF", headers={"Content-Type": "application/pdf"})
    client.reports.export_pdf("r1", html="<html></html>", file_name="x.pdf")
    assert fake.last.method == "POST"
    assert fake.last_json() == {"html": "<html></html>", "fileName": "x.pdf"}


def test_image_upload_multipart(client, fake):
    fake.queue(201, json={"_id": "img1"})
    client.images.upload(io.BytesIO(b"\x89PNG..."), report_id="r1")
    body = fake.last.body
    assert b'name="image"' in body
    assert b'name="reportId"' in body and b"r1" in body
    assert fake.last.headers["Content-Type"].startswith("multipart/form-data")


def test_upload_guesses_content_type_from_filename(client, fake):
    fake.queue(201, json={"_id": "img1"})
    client.images.upload(("shot.png", b"\x89PNG..."), report_id="r1")
    assert b"Content-Type: image/png" in fake.last.body


def test_success_data_envelope_is_unwrapped(client, fake):
    fake.queue(201, json={"success": True, "data": {"_id": "vt1", "name": "T"}})
    created = client.vulnerability_templates.create("T", ["EN"], [])
    assert created == {"_id": "vt1", "name": "T"}


def test_paginated_envelope_is_not_unwrapped(client, fake):
    envelope = {"success": True, "data": [], "pagination": {"page": 1}}
    fake.queue(200, json=envelope)
    assert client.reports.list(page=1) == envelope


def test_comments_list_unwraps_comments_key(client, fake):
    fake.queue(200, json={"comments": [{"_id": "c1"}], "counts": {"total": 1}})
    assert client.comments.list("r1", "s1") == [{"_id": "c1"}]


def test_template_revisions_unwrapped(client, fake):
    fake.queue(200, json={"success": True, "revisions": [{"id": "rev1"}]})
    assert client.templates.revisions("t1") == [{"id": "rev1"}]


def test_vuln_template_list_and_search_unwrap_count_envelope(client, fake):
    fake.queue(200, json={"success": True, "count": 1, "data": [{"_id": "vt1"}]})
    assert client.vulnerability_templates.list() == [{"_id": "vt1"}]

    fake.queue(200, json={"success": True, "count": 1, "data": [{"_id": "vt1"}]})
    assert client.vulnerability_templates.search("sqli") == [{"_id": "vt1"}]

    paginated = {"success": True, "data": [{"_id": "vt1"}], "pagination": {"page": 1}}
    fake.queue(200, json=paginated)
    assert client.vulnerability_templates.list(page=1) == paginated


def test_attachment_upload_from_path(client, fake, tmp_path):
    f = tmp_path / "evidence.txt"
    f.write_bytes(b"proof")
    fake.queue(201, json={"_id": "a1"})
    client.attachments.upload(str(f), report_id="r1")
    body = fake.last.body
    assert b'filename="evidence.txt"' in body
    assert b"proof" in body


def test_planning_event_create(client, fake):
    fake.queue(201, json={"_id": "e1"})
    client.planning.create_event(
        "Acme external",
        dt.datetime(2026, 8, 3, 9, 0),
        dt.datetime(2026, 8, 7, 18, 0),
        ["u1", "u2"],
        "pentest",
        color="#3B82F6",
    )
    sent = fake.last_json()
    assert sent["startDate"] == "2026-08-03T09:00:00"
    assert sent["assignees"] == ["u1", "u2"]
    assert sent["eventType"] == "pentest"
    assert "notes" not in sent


def test_planning_calendar_range_params(client, fake):
    fake.queue(200, json={})
    client.planning.calendar(dt.date(2026, 7, 1), dt.date(2026, 7, 31))
    assert fake.last_query() == {"start": ["2026-07-01"], "end": ["2026-07-31"]}


def test_comment_filters(client, fake):
    fake.queue(200, json=[])
    client.comments.list("r1", "s1", resolved=False, type="finding")
    q = fake.last_query()
    assert q["resolved"] == ["false"]
    assert q["type"] == ["finding"]


def test_note_toggle_pin(client, fake):
    fake.queue(200, json={})
    client.notes.toggle_pin("n1")
    assert fake.last.method == "PATCH"
    assert fake.last_path() == "/api/notes/n1/toggle-pin"


def test_snapshot_paths(client, fake):
    fake.queue(200, json={})
    client.snapshots.diff("r1", "s1")
    assert fake.last_path() == "/api/reports/r1/snapshots/s1/diff"


def test_vulnerability_template_set_report_templates(client, fake):
    fake.queue(200, json={})
    client.vulnerability_templates.set_report_templates("vt1", ["t1", "t2"])
    assert fake.last.method == "PUT"
    assert fake.last_json() == {"reportTemplateIds": ["t1", "t2"]}


def test_generic_request_escape_hatch(client, fake):
    fake.queue(200, json={"ok": True})
    assert client.request("GET", "health") == {"ok": True}
    assert fake.last_path() == "/api/health"
