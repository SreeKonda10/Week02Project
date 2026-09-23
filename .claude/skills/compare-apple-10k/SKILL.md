---
name: compare-apple-10k
description: Compare Apple's (AAPL) financial results across multiple fiscal years using their SEC 10-K filings — revenue, net income, gross/operating margin, diluted EPS, and product/segment revenue breakdown (iPhone, Mac, iPad, Services, etc). Use this whenever the user asks to compare Apple's financials across years, analyze Apple's 10-K, look at Apple's revenue/income trend, or wants numbers "from Apple's annual report" — even if they only name one year or don't mention "10-K" explicitly.
---

# Compare Apple 10-K filings across years

Pulls real numbers from SEC EDGAR — never estimate or recall figures from training data, since these change every fiscal year and the whole point is accuracy.

## Step 1 — Determine years to compare

Default to the last 3 fiscal years (Apple's fiscal year ends in late September — "FY2025" ended 2025-09-27) unless the user specifies different years or a different count.

## Step 2 — Core financial metrics (revenue, net income, margins, EPS)

Run the bundled script — it hits SEC's structured XBRL `companyconcept` API directly, so the numbers are exact rather than scraped/guessed from HTML:

```bash
python3 scripts/fetch_xbrl_metrics.py 2023 2024 2025
```

This prints a ready-to-use markdown table comparing Total Revenue, Net Income, Gross Margin, Operating Margin, and Diluted EPS across the given fiscal years. If a cell comes back `N/A`, the concept tag may differ for that year — check `references/known-filings.md` and consider fetching that year's 10-K directly to look up the figure by hand.

## Step 3 — Segment / product revenue breakdown

The XBRL `companyconcept` endpoint used in Step 2 only returns non-dimensional (whole-company) facts, so it can't give per-product numbers. **Do not WebFetch the full 10-K HTML for this** — it's huge (100+ pages) and gets summarized/truncated before reaching the financial statement notes, so the fetch will miss the data (confirmed by testing). Instead, use the filing's small, single-purpose XBRL "R.htm" report pages:

1. Get the filing's accession folder URL — same base path as the filing URL in `references/known-filings.md`, minus the `.htm` document name, e.g. `https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/`.
2. Fetch `FilingSummary.xml` from that folder (plain `curl`/`requests` with a descriptive `User-Agent`, same header as the script uses). Search its contents for a `<ShortName>` containing `"Revenue"` and `"Disaggregat"` (wording: "Revenue - Disaggregated Net Sales..."). Note the `<HtmlFileName>` a few lines above/below it (e.g. `R38.htm`) — this varies by filing year, so don't hardcode a specific R-number.
3. Fetch that specific `R##.htm` page (small — a few KB, safe to WebFetch or curl directly). It contains a clean table with net sales by product/segment (iPhone, Mac, iPad, Wearables Home and Accessories, Services) for **up to 3 comparative fiscal years in one page** — so one fetch from the most recent filing often covers your whole default 3-year comparison without needing older filings at all.
4. Only fall back to fetching an older filing's own `FilingSummary.xml` + R.htm if you need years outside what the most recent filing's comparative table covers.
5. If the note's title or structure differs for a given year (e.g. much older filings may call it "Products and Services Performance" instead of "Revenue"), search `FilingSummary.xml` more broadly for `"Product"` or `"Segment"` in `<ShortName>` to find the right R-file.

## Step 4 — Present the comparison

Combine Step 2's core-metrics table and Step 3's segment table into a single response. Call out notable trends (e.g., margin expansion, Services growth outpacing hardware) briefly — don't just dump tables with no interpretation.

## Notes

- SEC EDGAR requires a descriptive `User-Agent` header with contact info on all requests (`scripts/fetch_xbrl_metrics.py` already sets one) — requests without it get blocked with HTTP 403. If you hit rate limiting, slow down requests (SEC asks for ≤10 requests/second) and consider editing the contact email in the script.
- Apple's fiscal year label matches the calendar year its fiscal year *ends* in (FY2025 ended September 2025) — don't confuse this with the calendar year a filing was *made* in (the FY2025 10-K was filed in fall 2025).
- Do not fabricate numbers if a fetch fails — report what couldn't be retrieved and why, rather than filling in a plausible-looking guess.
