import io

import pytest

from vulnotes import VulnotesError


def test_report_dashboard_content_and_retest_contracts(client, fake):
    fake.queue(200, json={"reportsThisMonth": 2})
    assert client.reports.dashboard_stats()["reportsThisMonth"] == 2
    assert fake.last_path() == "/api/reports/dashboard/stats"

    fake.queue(200, json=[])
    client.reports.recent_activities(limit=7)
    assert fake.last_path() == "/api/reports/dashboard/activities"
    assert fake.last_query() == {"limit": ["7"]}

    fake.queue(200, json={})
    client.reports.update_content_section(
        "r1", "executiveSummary", content="Updated", is_complete=True
    )
    assert fake.last.method == "PUT"
    assert fake.last_path() == "/api/reports/r1/content/executiveSummary"
    assert fake.last_json() == {"content": "Updated", "isComplete": True}

    fake.queue(200, json={"finding": {"id": "f1"}})
    client.findings.complete_retest("r1", "f1", False, comment="Still vulnerable")
    assert fake.last_path() == "/api/reports/r1/findings/f1/retest"
    assert fake.last_json() == {"passed": False, "comment": "Still vulnerable"}


def test_snapshot_revert_contract(client, fake):
    fake.queue(200, json={"message": "Change reverted"})
    client.snapshots.revert_change(
        "r1", "s1", "finding-field", finding_id="f1", field_key="EN:impact"
    )
    assert fake.last.method == "POST"
    assert fake.last_path() == "/api/reports/r1/snapshots/s1/revert"
    assert fake.last_json() == {
        "target": "finding-field",
        "findingId": "f1",
        "fieldKey": "EN:impact",
    }


def test_complete_report_template_lifecycle_contracts(client, fake):
    fake.queue(201, json={"_id": "t1"})
    client.templates.create(
        "Pentest",
        language="en",
        vulnerability_templates=["vt1", "vt2"],
    )
    assert fake.last_path() == "/api/templates"
    assert fake.last_json() == {
        "name": "Pentest",
        "language": "en",
        "vulnerabilityTemplates": ["vt1", "vt2"],
    }

    fake.queue(200, json={})
    client.templates.update("t1", is_public=False, category_order=[])
    assert fake.last.method == "PUT"
    assert fake.last_json() == {"isPublic": False, "categoryOrder": []}

    fake.queue(201, json={})
    client.templates.clone("t1", name="Independent")
    assert fake.last_path() == "/api/templates/t1/clone"
    assert fake.last_json() == {"name": "Independent"}

    fake.queue(201, json={})
    client.templates.translate("t1", "fr")
    assert fake.last_path() == "/api/templates/t1/translate"
    assert fake.last_json() == {"language": "fr"}

    fake.queue(200, json={})
    client.templates.save_content("t1", [], global_styles="")
    assert fake.last_path() == "/api/templates/t1/content"
    assert fake.last_json() == {"htmlPages": [], "globalStyles": ""}

    fake.queue(200, json={})
    client.templates.clear_content("t1")
    assert fake.last.method == "DELETE"

    fake.queue(200, json={})
    client.templates.delete("t1")
    assert fake.last_path() == "/api/templates/t1"


def test_template_docx_import_is_multipart(client, fake):
    fake.queue(200, json={"success": True})
    client.templates.import_docx(("template.docx", io.BytesIO(b"docx")), language="fr")
    assert fake.last_path() == "/api/templates/import/docx"
    assert b'name="file"; filename="template.docx"' in fake.last.body
    assert b'name="language"' in fake.last.body
    assert b"fr" in fake.last.body


def test_attachment_and_planning_attachment_contracts(client, fake, tmp_path):
    fake.queue(200, content=b"evidence", headers={"Content-Type": "application/octet-stream"})
    target = tmp_path / "evidence.bin"
    assert client.attachments.download("a1", path=target) == b"evidence"
    assert fake.last_path() == "/api/attachments/a1/download"
    assert target.read_bytes() == b"evidence"

    fake.queue(201, json={"_id": "pa1"})
    client.planning.upload_attachment("e1", ("scope.txt", b"scope"))
    assert fake.last_path() == "/api/planning/events/e1/attachments"
    assert b'name="file"; filename="scope.txt"' in fake.last.body

    fake.queue(200, content=b"scope", headers={"Content-Type": "text/plain"})
    assert client.planning.download_attachment("e1", "pa1") == b"scope"
    assert fake.last_path() == "/api/planning/events/e1/attachments/pa1/download"

    fake.queue(200, json={"message": "deleted"})
    client.planning.delete_attachment("e1", "pa1")
    assert fake.last.method == "DELETE"
    assert fake.last_path() == "/api/planning/events/e1/attachments/pa1"


def test_description_only_ai_finding_and_shape_limits(client, fake):
    fake.queue(200, json={"success": True})
    client.ai.generate_finding_from_images("r1", description="Observed verbose error")
    assert fake.last_path() == "/api/ai/report/r1/generate-finding"
    assert "description=Observed+verbose+error" in fake.last.body

    with pytest.raises(ValueError, match="description is required"):
        client.ai.generate_finding_from_images("r1")
    with pytest.raises(ValueError, match="at most five"):
        client.ai.generate_finding_from_images("r1", [b"x"] * 6)


def test_new_mutations_validate_shapes_before_network(client, fake):
    with pytest.raises(ValueError, match="between 1 and 50"):
        client.reports.recent_activities(limit=0)
    with pytest.raises(ValueError, match="content or is_complete"):
        client.reports.update_content_section("r1", "summary")
    with pytest.raises(ValueError, match="exportType"):
        client.reports.import_json({"report": {"title": "Missing marker"}})
    with pytest.raises(TypeError, match="passed must be a boolean"):
        client.findings.complete_retest("r1", "f1", "yes")
    with pytest.raises(ValueError, match="field_key is required"):
        client.snapshots.revert_change(
            "r1", "s1", "finding-field", finding_id="f1"
        )
    with pytest.raises(ValueError, match="non-empty"):
        client.templates.create("  ")
    with pytest.raises(ValueError, match=r"\.docx"):
        client.templates.import_docx(("template.pdf", b"not-docx"))
    with pytest.raises(TypeError, match="html_pages must be a list"):
        client.templates.save_content("t1", {})
    assert fake.calls == []


@pytest.mark.parametrize(
    "bad_path",
    [
        "/reports/../../settings",
        "/reports/%2e%2e/%2e%2e/settings",
        "/reports/%252e%252e/%252e%252e/settings",
        "//attacker.example/api/reports",
        "/reports\\..\\settings",
    ],
)
def test_request_rejects_path_confusion_before_network(client, fake, bad_path):
    with pytest.raises(VulnotesError, match="Unsafe API path"):
        client.get(bad_path)
    assert fake.calls == []
