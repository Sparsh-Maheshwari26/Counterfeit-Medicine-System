"""Offline tests for paging and de-duplication in the reference sync client."""
from __future__ import annotations

import unittest
from unittest.mock import patch

from src.reference_sync import fetch_openfda_records


class FakeResponse:
    def __init__(self, results: list[dict]):
        self.status_code = 200
        self.ok = True
        self._results = results
        self.text = ""

    def json(self) -> dict:
        return {"results": self._results}


class FakeSession:
    def __init__(self):
        self.headers = {}

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def get(self, _url, params, timeout):
        start = params["skip"]
        end = start + params["limit"]
        rows = []
        for n in range(start, min(end, 500)):
            rows.append({
                "product_ndc": f"12345-{n:04d}",
                "brand_name": f"Example {n}",
                "generic_name": "Test ingredient",
                "labeler_name": "Test labeler",
            })
        return FakeResponse(rows)


class ReferenceSyncTests(unittest.TestCase):
    def test_fetches_target_as_unique_product_records(self) -> None:
        with patch("src.reference_sync.requests.Session", FakeSession):
            records = fetch_openfda_records(target=500)
        self.assertEqual(len(records), 500)
        self.assertEqual(len({r["product_ndc"] for r in records}), 500)
        self.assertEqual(records[-1]["product_ndc"], "12345-0499")


if __name__ == "__main__":
    unittest.main()
