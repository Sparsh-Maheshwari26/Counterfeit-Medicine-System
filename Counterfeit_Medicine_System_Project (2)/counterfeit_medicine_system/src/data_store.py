"""SQLite storage for medicine reference records.

Official records are reference listings from openFDA's NDC Directory. They are
not batch-level authentication records and are not independently verified by
this application.
"""
from __future__ import annotations

import csv
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "medicine_reference.db"
DEMO_CSV = DATA_DIR / "demo_medicines.csv"
SOURCE_URL = "https://open.fda.gov/apis/drug/ndc/"

COLUMNS = [
    "record_key", "brand_name", "generic_name", "active_ingredients", "strength",
    "labeler_name", "product_ndc", "package_ndc", "dosage_form", "route",
    "product_type", "marketing_start_date", "marketing_end_date",
    "listing_expiration_date", "manufacturer_country", "source_type", "source_name",
    "source_url", "synced_at",
]


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def connect() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=20)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def db_connection():
    """Connection context that commits/rolls back and always closes SQLite."""
    conn = connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    with db_connection() as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS medicine_reference (
                record_key TEXT PRIMARY KEY,
                brand_name TEXT NOT NULL DEFAULT '',
                generic_name TEXT NOT NULL DEFAULT '',
                active_ingredients TEXT NOT NULL DEFAULT '',
                strength TEXT NOT NULL DEFAULT '',
                labeler_name TEXT NOT NULL DEFAULT '',
                product_ndc TEXT NOT NULL DEFAULT '',
                package_ndc TEXT NOT NULL DEFAULT '',
                dosage_form TEXT NOT NULL DEFAULT '',
                route TEXT NOT NULL DEFAULT '',
                product_type TEXT NOT NULL DEFAULT '',
                marketing_start_date TEXT NOT NULL DEFAULT '',
                marketing_end_date TEXT NOT NULL DEFAULT '',
                listing_expiration_date TEXT NOT NULL DEFAULT '',
                manufacturer_country TEXT NOT NULL DEFAULT '',
                source_type TEXT NOT NULL DEFAULT 'demo',
                source_name TEXT NOT NULL DEFAULT '',
                source_url TEXT NOT NULL DEFAULT '',
                synced_at TEXT NOT NULL DEFAULT ''
            )"""
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_medicine_brand ON medicine_reference(brand_name)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_medicine_generic ON medicine_reference(generic_name)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_medicine_labeler ON medicine_reference(labeler_name)")
        count = conn.execute("SELECT COUNT(*) FROM medicine_reference").fetchone()[0]
        if count == 0:
            _seed_demo_records(conn)


def _seed_demo_records(conn: sqlite3.Connection) -> None:
    """Seed only clearly labelled fictional rows so the UI works offline."""
    if not DEMO_CSV.exists():
        return
    with DEMO_CSV.open("r", newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        return
    now = _utc_now()
    prepared = []
    for i, row in enumerate(rows, start=1):
        item = {column: str(row.get(column, "") or "") for column in COLUMNS}
        item["record_key"] = item["record_key"] or f"DEMO-{i:04d}"
        item["source_type"] = "demo"
        item["source_name"] = "Fictional UI demo data, not an actual medicine registry"
        item["source_url"] = ""
        item["synced_at"] = now
        prepared.append(tuple(item[column] for column in COLUMNS))
    placeholders = ",".join("?" for _ in COLUMNS)
    conn.executemany(
        f"INSERT OR IGNORE INTO medicine_reference ({','.join(COLUMNS)}) VALUES ({placeholders})",
        prepared,
    )


def get_all_records(source_type: str | None = None) -> list[dict[str, Any]]:
    init_db()
    with db_connection() as conn:
        if source_type:
            rows = conn.execute(
                "SELECT * FROM medicine_reference WHERE source_type = ? ORDER BY brand_name COLLATE NOCASE",
                (source_type,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM medicine_reference ORDER BY source_type DESC, brand_name COLLATE NOCASE"
            ).fetchall()
        return [dict(row) for row in rows]


def get_counts() -> dict[str, int]:
    init_db()
    with db_connection() as conn:
        result = conn.execute(
            "SELECT source_type, COUNT(*) AS n FROM medicine_reference GROUP BY source_type"
        ).fetchall()
    counts = {str(row["source_type"]): int(row["n"]) for row in result}
    return {"official": counts.get("official_openfda", 0), "demo": counts.get("demo", 0), "total": sum(counts.values())}


def save_openfda_records(records: Iterable[dict[str, Any]]) -> int:
    """Replace the official-reference portion after a successful sync."""
    init_db()
    now = _utc_now()
    prepared: list[tuple[str, ...]] = []
    seen: set[str] = set()
    for rec in records:
        product_ndc = str(rec.get("product_ndc") or "").strip()
        brand = str(rec.get("brand_name") or "").strip()
        generic = str(rec.get("generic_name") or "").strip()
        labeler = str(rec.get("labeler_name") or "").strip()
        if not (product_ndc or brand or generic):
            continue
        key = product_ndc or "|".join((brand, generic, labeler))
        if key in seen:
            continue
        seen.add(key)
        ingredients = rec.get("active_ingredients") or []
        if isinstance(ingredients, list):
            ingredient_text = "; ".join(
                " ".join(str(x) for x in [ing.get("name", ""), ing.get("strength", "")] if x)
                if isinstance(ing, dict) else str(ing)
                for ing in ingredients
            )
        else:
            ingredient_text = str(ingredients)
        packages = rec.get("packaging") or []
        package_ndc = ""
        if isinstance(packages, list) and packages:
            first = packages[0]
            if isinstance(first, dict):
                package_ndc = str(first.get("package_ndc") or "")
        values = {
            "record_key": key,
            "brand_name": brand,
            "generic_name": generic,
            "active_ingredients": ingredient_text,
            "strength": ingredient_text,
            "labeler_name": labeler,
            "product_ndc": product_ndc,
            "package_ndc": package_ndc,
            "dosage_form": str(rec.get("dosage_form") or ""),
            "route": ", ".join(rec.get("route") or []) if isinstance(rec.get("route"), list) else str(rec.get("route") or ""),
            "product_type": str(rec.get("product_type") or ""),
            "marketing_start_date": str(rec.get("marketing_start_date") or ""),
            "marketing_end_date": str(rec.get("marketing_end_date") or ""),
            "listing_expiration_date": str(rec.get("listing_expiration_date") or ""),
            "manufacturer_country": "",
            "source_type": "official_openfda",
            "source_name": "openFDA NDC Directory, labeler-submitted listing",
            "source_url": SOURCE_URL,
            "synced_at": now,
        }
        prepared.append(tuple(values[col] for col in COLUMNS))
    if not prepared:
        raise ValueError("No usable product records were returned by the reference source.")
    placeholders = ",".join("?" for _ in COLUMNS)
    with db_connection() as conn:
        conn.execute("DELETE FROM medicine_reference WHERE source_type = 'official_openfda'")
        conn.executemany(
            f"INSERT OR REPLACE INTO medicine_reference ({','.join(COLUMNS)}) VALUES ({placeholders})",
            prepared,
        )
    return len(prepared)


def search_records(query: str, limit: int = 40, include_demo: bool = True) -> list[dict[str, Any]]:
    """Search reference fields using parameterized SQL and case-insensitive matching."""
    init_db()
    q = (query or "").strip()
    if not q:
        return []
    pattern = f"%{q}%"
    source_filter = "" if include_demo else "AND source_type = 'official_openfda'"
    with db_connection() as conn:
        rows = conn.execute(
            f"""SELECT * FROM medicine_reference
                WHERE (brand_name LIKE ? COLLATE NOCASE
                   OR generic_name LIKE ? COLLATE NOCASE
                   OR active_ingredients LIKE ? COLLATE NOCASE
                   OR labeler_name LIKE ? COLLATE NOCASE
                   OR product_ndc LIKE ? COLLATE NOCASE
                   OR package_ndc LIKE ? COLLATE NOCASE)
                   {source_filter}
                ORDER BY CASE WHEN source_type = 'official_openfda' THEN 0 ELSE 1 END,
                         brand_name COLLATE NOCASE
                LIMIT ?""",
            (pattern, pattern, pattern, pattern, pattern, pattern, int(limit)),
        ).fetchall()
        return [dict(row) for row in rows]
