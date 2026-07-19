"""Create a report and push scanner findings into it.

Set VULNOTES_URL and VULNOTES_API_KEY before running (the key needs
rw:reports and, to link a company, ro:clients).
"""

from vulnotes import VulnotesClient

# Pretend output of a scanner
SCANNER_RESULTS = [
    {
        "name": "Outdated OpenSSH (9.0p1)",
        "severity": "Medium",
        "hosts": ["203.0.113.10"],
        "detail": "The SSH service reports an outdated version with known CVEs.",
    },
    {
        "name": "TLS certificate expired",
        "severity": "Low",
        "hosts": ["203.0.113.12"],
        "detail": "The certificate served on port 443 expired 42 days ago.",
    },
]


def main() -> None:
    client = VulnotesClient()

    report = client.reports.create("Perimeter scan import", language="EN")
    print(f"Created report {report['_id']}")

    for issue in SCANNER_RESULTS:
        finding = client.findings.add(
            report["_id"],
            {
                "title": issue["name"],
                "severity": issue["severity"],
                "affectedSystems": issue["hosts"],
                "data": {"EN": {"title": issue["name"], "description": issue["detail"]}},
            },
        )
        print(f"  added finding {finding['id']}: {issue['name']}")


if __name__ == "__main__":
    main()
