"""Small, testable helpers for screening medicine label details.

These helpers compare only product-level reference listings. They never
establish the authenticity of a physical pack or manufacturing batch.
"""
from __future__ import annotations

import re
from typing import Any, Iterable


def clean_text(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def normalize_product_code(value: object) -> str:
    """Normalize punctuation and spacing for exact product-code comparisons."""
    return re.sub(r"[^a-z0-9]", "", clean_text(value).casefold())


def record_matches_name(record: dict[str, Any], query: str) -> bool:
    """Match a label query against product, generic and ingredient fields."""
    q = clean_text(query).casefold()
    if not q:
        return False
    fields = [record.get("brand_name", ""), record.get("generic_name", ""), record.get("active_ingredients", "")]
    for field in fields:
        val = clean_text(field).casefold()
        if q in val or val in q:
            return True
    q_tokens = [token for token in re.findall(r"[a-z0-9]+", q) if len(token) > 2]
    searchable = " ".join(clean_text(field).casefold() for field in fields)
    return bool(q_tokens) and sum(token in searchable for token in q_tokens) / len(q_tokens) >= 0.7


def select_official_matches(
    records: Iterable[dict[str, Any]], medicine_name: str, product_code: str = ""
) -> tuple[list[dict[str, Any]], str]:
    """Return reference matches and a label explaining which fields matched.

    Supported cases:
      - name_only: product name matched, no code was entered
      - name_and_code: both name and product/package NDC matched
      - code_mismatch: name matched, entered code did not match
      - code_name_mismatch: code matched a record, entered name did not
      - no_match: no useful match was found
    """
    all_records = list(records)
    name_matches = [record for record in all_records if record_matches_name(record, medicine_name)]
    entered_code = normalize_product_code(product_code)
    if not entered_code:
        return name_matches, "name_only" if name_matches else "no_match"

    code_matches = []
    for record in all_records:
        product_ndc = normalize_product_code(record.get("product_ndc"))
        package_ndc = normalize_product_code(record.get("package_ndc"))
        if entered_code and entered_code in {product_ndc, package_ndc}:
            code_matches.append(record)

    if code_matches:
        combined_matches = [record for record in code_matches if record_matches_name(record, medicine_name)]
        if combined_matches:
            return combined_matches, "name_and_code"
        return code_matches, "code_name_mismatch"

    if name_matches:
        return name_matches, "code_mismatch"
    return [], "no_match"
