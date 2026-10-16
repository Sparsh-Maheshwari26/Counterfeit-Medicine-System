"""Offline tests for name and exact product-code screening logic."""
from __future__ import annotations

import unittest

from src.verification import normalize_product_code, record_matches_name, select_official_matches


class VerificationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.records = [
            {
                "record_key": "REF-1",
                "brand_name": "SampleCare Paracetamol",
                "generic_name": "Paracetamol",
                "active_ingredients": "Paracetamol 500 mg",
                "product_ndc": "12345-6789",
                "package_ndc": "12345-6789-01",
                "labeler_name": "SampleCare Labs",
            },
            {
                "record_key": "REF-2",
                "brand_name": "Other Relief",
                "generic_name": "Ibuprofen",
                "active_ingredients": "Ibuprofen 200 mg",
                "product_ndc": "54321-2222",
                "package_ndc": "54321-2222-10",
                "labeler_name": "Other Labs",
            },
        ]

    def test_normalizes_punctuation_for_codes(self) -> None:
        self.assertEqual(normalize_product_code("12345-6789"), "123456789")
        self.assertEqual(normalize_product_code("12345 6789"), "123456789")

    def test_name_and_code_both_match(self) -> None:
        matches, case = select_official_matches(self.records, "SampleCare Paracetamol", "12345-6789")
        self.assertEqual(case, "name_and_code")
        self.assertEqual([row["record_key"] for row in matches], ["REF-1"])

    def test_name_match_does_not_hide_wrong_code(self) -> None:
        matches, case = select_official_matches(self.records, "SampleCare Paracetamol", "99999-0000")
        self.assertEqual(case, "code_mismatch")
        self.assertEqual([row["record_key"] for row in matches], ["REF-1"])

    def test_code_match_does_not_hide_wrong_name(self) -> None:
        matches, case = select_official_matches(self.records, "Ibuprofen", "12345-6789")
        self.assertEqual(case, "code_name_mismatch")
        self.assertEqual([row["record_key"] for row in matches], ["REF-1"])

    def test_unknown_name_and_code_returns_no_match(self) -> None:
        matches, case = select_official_matches(self.records, "Unknown Product", "99999-0000")
        self.assertEqual(case, "no_match")
        self.assertEqual(matches, [])

    def test_blank_query_does_not_match(self) -> None:
        self.assertFalse(record_matches_name(self.records[0], ""))


if __name__ == "__main__":
    unittest.main()
