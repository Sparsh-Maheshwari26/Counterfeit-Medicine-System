"""Fetch product reference listings from the openFDA NDC Directory."""
from __future__ import annotations

import time
from typing import Any

import requests

API_URL = "https://api.fda.gov/drug/ndc.json"
SOURCE_URL = "https://open.fda.gov/apis/drug/ndc/"
USER_AGENT = "CounterfeitMedicineSystemStudentProject/1.0 (educational reference lookup)"


def fetch_openfda_records(target: int = 500, page_size: int = 100, timeout: int = 25) -> list[dict[str, Any]]:
    """Fetch at least `target` unique finished-product listing records.

    openFDA permits up to 100 results per request. The returned records are
    labeler-submitted listings, not verified batch records or proof of approval.
    """
    if target < 1:
        raise ValueError("target must be at least 1")
    page_size = min(max(int(page_size), 1), 100)
    all_records: list[dict[str, Any]] = []
    seen: set[str] = set()
    skip = 0
    max_pages = max(10, (target // page_size) + 10)

    with requests.Session() as session:
        session.headers.update({"User-Agent": USER_AGENT, "Accept": "application/json"})
        for _ in range(max_pages):
            params = {"search": "finished:true", "limit": page_size, "skip": skip}
            try:
                response = session.get(API_URL, params=params, timeout=timeout)
            except requests.RequestException as exc:
                raise RuntimeError(
                    "Could not connect to openFDA. Check your internet connection and try again."
                ) from exc

            if response.status_code == 404:
                # openFDA returns 404 for a search with no matching rows.
                break
            if response.status_code == 429:
                time.sleep(2)
                response = session.get(API_URL, params=params, timeout=timeout)
            if not response.ok:
                detail = ""
                try:
                    detail = response.json().get("error", {}).get("message", "")
                except Exception:
                    detail = response.text[:180]
                raise RuntimeError(f"openFDA returned HTTP {response.status_code}. {detail}".strip())
            try:
                payload = response.json()
            except ValueError as exc:
                raise RuntimeError("openFDA returned an unreadable response.") from exc
            page = payload.get("results", [])
            if not page:
                break
            for rec in page:
                key = str(rec.get("product_ndc") or "").strip()
                if not key:
                    key = "|".join([
                        str(rec.get("brand_name") or ""),
                        str(rec.get("generic_name") or ""),
                        str(rec.get("labeler_name") or ""),
                    ])
                if key and key not in seen:
                    all_records.append(rec)
                    seen.add(key)
                    if len(all_records) >= target:
                        return all_records[:target]
            if len(page) < page_size:
                break
            skip += page_size

    if len(all_records) < target:
        raise RuntimeError(
            f"The source returned {len(all_records)} unique records, fewer than the requested {target}. "
            "The existing database was left unchanged. Try again later or lower the target in the sync script."
        )
    return all_records[:target]
