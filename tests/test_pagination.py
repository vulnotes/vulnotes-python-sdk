def envelope(items, page, total_pages):
    return {
        "success": True,
        "data": items,
        "pagination": {
            "page": page,
            "limit": len(items),
            "total": None,
            "totalPages": total_pages,
            "hasNextPage": page < total_pages,
        },
    }


def test_iter_pages_through_envelope(client, fake):
    fake.queue(200, json=envelope([{"_id": "1"}, {"_id": "2"}], 1, 2))
    fake.queue(200, json=envelope([{"_id": "3"}], 2, 2))
    items = list(client.reports.iter(limit=2))
    assert [i["_id"] for i in items] == ["1", "2", "3"]
    assert len(fake.calls) == 2
    assert fake.last_query() == {"page": ["2"], "limit": ["2"]}


def test_iter_supports_legacy_flat_envelope(client, fake):
    fake.queue(200, json={"data": [{"_id": "1"}], "total": 2, "page": 1, "totalPages": 2})
    fake.queue(200, json={"data": [{"_id": "2"}], "total": 2, "page": 2, "totalPages": 2})
    items = list(client.reports.iter(limit=1))
    assert [i["_id"] for i in items] == ["1", "2"]


def test_iter_handles_plain_list_response(client, fake):
    fake.queue(200, json=[{"_id": "1"}, {"_id": "2"}])
    items = list(client.companies.iter())
    assert len(items) == 2
    assert len(fake.calls) == 1


def test_iter_stops_on_empty_page(client, fake):
    fake.queue(200, json={"data": [], "total": 0, "page": 1, "totalPages": 0})
    assert list(client.vulnerabilities.iter()) == []


def test_list_without_params_sends_no_query(client, fake):
    fake.queue(200, json=[])
    client.reports.list()
    assert fake.last_query() == {}


def test_list_with_params(client, fake):
    fake.queue(200, json={"data": [], "totalPages": 0})
    client.reports.list(page=2, limit=50)
    assert fake.last_query() == {"page": ["2"], "limit": ["50"]}
