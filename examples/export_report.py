"""Export a report as JSON and PDF.

Usage: python export_report.py <report_id>
Set VULNOTES_URL and VULNOTES_API_KEY first (the key needs ro:reports).
"""

import json
import sys

from vulnotes import NotFoundError, VulnotesClient


def main(report_id: str) -> None:
    client = VulnotesClient()

    export = client.reports.export_json(report_id)
    with open(f"report-{report_id}.json", "w") as fh:
        json.dump(export, fh, indent=2)
    print(f"Wrote report-{report_id}.json")

    try:
        # PDF archived when the report was marked completed (pixel-perfect)
        client.reports.archived_pdf(report_id, path=f"report-{report_id}.pdf")
    except NotFoundError:
        # Not completed yet: fall back to server-side rendering
        client.reports.export_pdf(report_id, path=f"report-{report_id}.pdf")
    print(f"Wrote report-{report_id}.pdf")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
