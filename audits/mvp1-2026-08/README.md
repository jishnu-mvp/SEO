# mvp1.com.au — Organic Search Audit (August 2026)

Full technical + content audit, May–August 2026 month-by-month comparison, and
claim-by-claim verification of 34 external agency deliverables against live
Search Console and GA4 data.

**Report:** `mvp1-organic-search-audit.html` (published as a Claude Artifact)
**PDF:** `MVP1-Organic-Search-Audit-Aug2026.pdf` (A4, 11pp, brand fonts embedded)
**Vendor email:** `agency-email-draft.md` (draft, not sent)

## Headline findings

| Metric (April benchmark → August) | Change |
|---|---|
| Organic clicks 202 → 103 | −49% |
| Impressions 4,832 → 1,945 | −60% |
| Average position 8.4 → 16.4 | −8.0 places |
| Non-branded clicks | 0–1/month throughout |
| Mapped keyword targets ranking | 1 of 17 |

15 vendor claims adjudicated: **6 contradicted, 3 hollow, 2 partly verified, 4 verified**.

A critical credential-exposure issue was found in the vendor's publicly-shared
Drive folder. Those files are deliberately **not** committed here.

## Reproducing

Requires `GOOGLE_APPLICATION_CREDENTIALS`, `GSC_PROPERTY`, `GA4_PROPERTY_ID`.

```bash
python3 scripts/gsc_pull.py    # Search Console, Mar–Aug 2026
python3 scripts/ga4_pull.py    # GA4 monthly, by channel/device/landing page
python3 scripts/crawl.py       # crawl all sitemap URLs, extract on-page SEO
python3 scripts/pr_check.py    # sample PR backlinks for liveness + dofollow
python3 scripts/extract.py     # parse vendor PDF/XLS/XLSX/DOCX deliverables
python3 scripts/makepdf.py     # render the HTML report to A4 PDF via headless Chromium
```

`data/` holds the raw pulls behind every figure in the report.

## Method limits

- August Search Console data runs to the 30th (31st not yet published).
- Branded/non-branded split uses query-level rows covering 62–79% of clicks;
  Google withholds the remainder under its privacy threshold.
- Only the URL-prefix property was readable, not a domain property.
- Business Profile console was not accessible; GBP figures are corroborated
  via GA4 rather than proven.
- No Core Web Vitals field data — the configured API key is invalid and the
  PageSpeed quota was exhausted.
