# vulnotes-python-sdk

Python client for the [Vulnotes](https://vulnotes.com) REST API.

```bash
pip install vulnotes
```

Needs Python 3.9 or later. The only dependency is `requests`.

## Getting started

Create an API key in Vulnotes under Settings > API Keys, then:

```python
from vulnotes import VulnotesClient

client = VulnotesClient("https://acme.vulnotes.app", api_key="vuln_sk_...")

report = client.reports.create("External pentest Q3", language="EN")

client.findings.add(report["_id"], {
    "title": "SQL Injection in /login",
    "severity": "Critical",
    "cvss": {"vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"},
    "data": {"EN": {"title": "SQL Injection in /login", "description": "..."}},
})
```

If `VULNOTES_URL` and `VULNOTES_API_KEY` are set in the environment you can just do `VulnotesClient()`.

Methods return plain dicts and lists matching the API's JSON. File exports return bytes. If you're wondering what a key is allowed to do, `client.api_keys.me()` tells you.

## What's covered

Everything reachable with an operational API key: reports and findings, companies, the vulnerability library, full report-template authoring, snapshots and review comments, notes, image/attachment management, exports, the planning calendar (including event attachments), and AI-assisted authoring. This operational parity work does not expand administrative settings or client-portal namespaces. Full SDK reference: [docs.vulnotes.com/api/python-sdk](https://docs.vulnotes.com/api/python-sdk).

Anything not wrapped yet can still be called directly:

```python
client.request("GET", f"/reports/{report_id}/snapshots")
```

## A few common tasks

Iterating without dealing with pages:

```python
for report in client.reports.iter():
    print(report["title"])
```

Feeding scanner results into a report:

```python
for issue in results:
    client.findings.add(report_id, {
        "title": issue["name"],
        "severity": issue["severity"],
        "affectedSystems": issue["hosts"],
        "data": {"EN": {"title": issue["name"], "description": issue["detail"]}},
    })
```

Downloading exports:

```python
client.reports.export_xlsx(report_id, finding_fields=["title", "severity"], path="findings.xlsx")
client.reports.archived_pdf(report_id, path="final.pdf")  # PDF stored when the report was completed
```

Uploading evidence:

```python
client.images.upload("screenshot.png", report_id=report_id)
client.attachments.upload("nmap-scan.xml", report_id=report_id)
client.attachments.download(attachment_id, path="downloaded-scan.xml")
client.planning.upload_attachment(event_id, "scope.pdf")
```

Creating and saving a report template:

```python
template = client.templates.create("External pentest", language="en")
client.templates.save_content(
    template["_id"],
    html_pages=[{"id": "cover", "html": "<h1>{{ report.title }}</h1>"}],
    global_styles="h1 { color: #111827; }",
)
```

Dates can be passed as ISO strings or as `datetime.date`/`datetime.datetime`.

## Errors

Everything raised by the SDK inherits from `vulnotes.VulnotesError`. HTTP errors map to subclasses (`NotFoundError`, `PermissionDeniedError`, `RateLimitError`, ...) with `status_code`, `message` and the parsed body attached.

```python
from vulnotes import NotFoundError

try:
    client.reports.get(report_id)
except NotFoundError:
    # doesn't exist, or the key's owner can't see it
    ...
```

A key that lacks the permission an endpoint needs gets a `PermissionDeniedError` naming it. Reports outside the owner's visibility raise `NotFoundError`, not 403; that's intentional on the server side.

Idempotent requests are retried automatically on connection errors and 429/502/503/504. Tune with `max_retries`, `timeout` and `verify_ssl` on the client.
