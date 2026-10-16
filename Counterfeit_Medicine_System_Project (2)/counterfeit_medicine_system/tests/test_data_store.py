"""Offline tests for the local reference database layer."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src import data_store


class DataStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_db_path = data_store.DB_PATH
        data_store.DB_PATH = Path(self.temp_dir.name) / "test_medicine_reference.db"
        data_store.init_db()

    def tearDown(self) -> None:
        data_store.DB_PATH = self.original_db_path
        self.temp_dir.cleanup()

    def test_demo_rows_are_labelled_demo(self) -> None:
        counts = data_store.get_counts()
        self.assertEqual(counts["official"], 0)
        self.assertEqual(counts["demo"], 12)
        matches = data_store.search_records("paracetamol", include_demo=True)
        self.assertTrue(matches)
        self.assertEqual(matches[0]["source_type"], "demo")

    def test_save_500_unique_listing_records(self) -> None:
        records = []
        for number in range(500):
            records.append({
                "product_ndc": f"99999-{number:04d}",
                "brand_name": f"Test Brand {number}",
                "generic_name": f"Test Ingredient {number}",
                "active_ingredients": [{"name": f"Test Ingredient {number}", "strength": "10 mg"}],
                "labeler_name": "Example labeler used only in this offline test",
                "packaging": [{"package_ndc": f"99999-{number:04d}-01"}],
                "dosage_form": "TABLET",
                "route": ["ORAL"],
                "product_type": "TEST FIXTURE",
                "finished": True,
            })
        saved = data_store.save_openfda_records(records)
        counts = data_store.get_counts()
        self.assertEqual(saved, 500)
        self.assertEqual(counts["official"], 500)
        self.assertEqual(counts["demo"], 12)
        found = data_store.search_records("Test Brand 314", include_demo=False)
        self.assertTrue(any(row["brand_name"] == "Test Brand 314" for row in found))


if __name__ == "__main__":
    unittest.main()
