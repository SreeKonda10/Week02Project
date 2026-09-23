#!/usr/bin/env python3
"""Fetch and compare core financial metrics from Apple's 10-K filings via SEC EDGAR's XBRL API.

Usage:
    python fetch_xbrl_metrics.py [FY ...]

    python fetch_xbrl_metrics.py 2023 2024 2025

If no fiscal years are given, defaults to the last 3 (2023, 2024, 2025).

Pulls: total revenue, net income, gross margin, operating margin, diluted EPS.
Does NOT cover segment/product revenue breakdown -- that requires dimensional
XBRL data that this endpoint doesn't cleanly expose. For that, fetch the
specific 10-K's "Segment Information" note directly (see SKILL.md).
"""

import json
import sys
import urllib.request
from datetime import date

CIK = "0000320193"  # Apple Inc.

# SEC requires a descriptive User-Agent identifying the requester + contact info.
# Replace the email below with your own if you hit rate limiting (HTTP 403).
USER_AGENT = "compare-apple-10k-skill (contact: your-email@example.com)"

# Each metric tries tags in order -- Apple switched primary revenue tags over time.
CONCEPTS = {
    "Total Revenue": ["RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues"],
    "Net Income": ["NetIncomeLoss"],
    "Gross Profit": ["GrossProfit"],
    "Operating Income": ["OperatingIncomeLoss"],
    "Diluted EPS": ["EarningsPerShareDiluted"],
}


def fetch_concept(cik: str, tag: str):
    url = f"https://data.sec.gov/api/xbrl/companyconcept/CIK{cik}/us-gaap/{tag}.json"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.load(resp)
    except Exception:
        return None


def annual_values(data: dict) -> dict:
    """Return {fiscal_year_end_date: fact} for full-year (10-K, FY) facts, deduped by end date."""
    if not data:
        return {}
    units = data.get("units", {})
    series = units.get("USD") or units.get("USD/shares") or next(iter(units.values()), [])
    result = {}
    for entry in series:
        if entry.get("form") != "10-K" or entry.get("fp") != "FY":
            continue
        start, end = entry.get("start"), entry.get("end")
        if start and end:
            days = (date.fromisoformat(end) - date.fromisoformat(start)).days
            if not (350 <= days <= 380):
                continue  # skip partial-year / quarterly-shaped facts
        existing = result.get(end)
        if existing is None or entry.get("filed", "") > existing.get("filed", ""):
            result[end] = entry
    return result


def get_metric_by_fy(cik: str, tags: list, fiscal_years: list) -> dict:
    for tag in tags:
        data = fetch_concept(cik, tag)
        facts = annual_values(data)
        if facts:
            by_fy = {int(end[:4]): fact["val"] for end, fact in facts.items()}
            result = {fy: by_fy.get(fy) for fy in fiscal_years}
            if any(v is not None for v in result.values()):
                return result
    return dict.fromkeys(fiscal_years)


def fmt_usd(v):
    return f"${v / 1e9:.1f}B" if v is not None else "N/A"


def fmt_pct(v):
    return f"{v:.1f}%" if v is not None else "N/A"


def fmt_eps(v):
    return f"${v:.2f}" if v is not None else "N/A"


def main():
    fiscal_years = [int(y) for y in sys.argv[1:]] or [2023, 2024, 2025]

    metrics = {label: get_metric_by_fy(CIK, tags, fiscal_years) for label, tags in CONCEPTS.items()}

    gross_margin, operating_margin = {}, {}
    for fy in fiscal_years:
        rev = metrics["Total Revenue"].get(fy)
        gp = metrics["Gross Profit"].get(fy)
        oi = metrics["Operating Income"].get(fy)
        gross_margin[fy] = (gp / rev * 100) if rev and gp is not None else None
        operating_margin[fy] = (oi / rev * 100) if rev and oi is not None else None

    header = "| Metric | " + " | ".join(f"FY{fy}" for fy in fiscal_years) + " |"
    sep = "|---" + "|---" * len(fiscal_years) + "|"
    rows = [
        "| Total Revenue | " + " | ".join(fmt_usd(metrics["Total Revenue"].get(fy)) for fy in fiscal_years) + " |",
        "| Net Income | " + " | ".join(fmt_usd(metrics["Net Income"].get(fy)) for fy in fiscal_years) + " |",
        "| Gross Margin | " + " | ".join(fmt_pct(gross_margin.get(fy)) for fy in fiscal_years) + " |",
        "| Operating Margin | " + " | ".join(fmt_pct(operating_margin.get(fy)) for fy in fiscal_years) + " |",
        "| Diluted EPS | " + " | ".join(fmt_eps(metrics["Diluted EPS"].get(fy)) for fy in fiscal_years) + " |",
    ]

    print(header)
    print(sep)
    print("\n".join(rows))


if __name__ == "__main__":
    main()
