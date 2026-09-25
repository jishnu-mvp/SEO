#!/usr/bin/env python3
"""
Google Business Profile data-freshness guard.

This exists because of a specific, documented failure. On 24-25 Sep 2026 a
GBP daily series for mvp1.com.au was read straight out of the connector and
analysed as though it were final. It was not. Google had published nothing
for 14-24 September, so the series carried eleven trailing zeros, and those
zeros were averaged in and reported as a collapse in profile views. The
founder was told the listing was declining. It was not -- 1-13 September was
the strongest stretch on record at 10.4 impressions/day against 8.0 in
August.

The cause is that GBP performance data is not real-time:

  * daily impression metrics settle roughly 11-12 days behind "today"
  * monthly search-keyword data publishes only after the month closes

An unpublished day and a genuine zero look identical in the response. The
connector is not at fault and there is no setting to change -- the data
arrives later, exactly as August's did. What has to change is that a caller
must never mistake "not yet published" for "nobody came".

Two independent signals detect an incomplete tail, and this module checks
both, because either alone can miss:

1. Trailing zeros. Impressions reading zero on the most recent days for a
   listing that otherwise averages several per day.

2. Interactions exceeding impressions. A day showing more direction requests,
   website clicks or calls than impressions is arithmetically impossible --
   every interaction requires an impression to precede it. This catches a
   partially-published day that trailing-zero detection lets through, and it
   is what proved the September gap: 16 Sep reported 1 impression alongside
   12 direction requests.

Usage:
    python gbp_freshness.py --series gbp-daily.json
    python gbp_freshness.py --series gbp-daily.json --json
    python gbp_freshness.py --series gbp-daily.json --trim > settled.json
    python gbp_freshness.py --cutoff --asof 2026-09-25

Exit status is 1 when the series is unsafe to report on as-is, so this can
gate a run the same way audit_coverage.py --validate does.
"""

import argparse
import datetime
import json
import sys

# Google settles daily impression metrics ~11-12 days back. 14 gives margin
# without discarding much: a weekly report reads a window that closed a
# fortnight ago, which is still current enough to act on.
SETTLE_LAG_DAYS = 14

# Metrics that cannot exceed impressions on the same day.
INTERACTION_FIELDS = (
    "website_clicks",
    "call_clicks",
    "direction_requests",
    "business_bookings",
    "business_food_orders",
    "business_food_menu_clicks",
)


def _as_date(value):
    """Accept 'YYYY-MM-DD', a date, or a datetime; return a date."""
    if isinstance(value, datetime.datetime):
        return value.date()
    if isinstance(value, datetime.date):
        return value
    return datetime.date.fromisoformat(str(value)[:10])


def settled_cutoff(asof=None, lag_days=SETTLE_LAG_DAYS):
    """The most recent date whose GBP metrics can be treated as final."""
    asof = _as_date(asof) if asof else datetime.date.today()
    return asof - datetime.timedelta(days=lag_days)


def _rows(series):
    """Normalise the connector's shapes into a list of row dicts."""
    if isinstance(series, dict):
        series = series.get("result", series.get("rows", series.get("data", [])))
    return [r for r in series if isinstance(r, dict) and r.get("date")]


def inspect(series, asof=None, lag_days=SETTLE_LAG_DAYS):
    """Report whether a GBP daily series is safe to analyse.

    Returns a dict carrying the settled cutoff, the rows that fall after it,
    and every row this module can prove is incomplete.
    """
    rows = sorted(_rows(series), key=lambda r: str(r["date"]))
    cutoff = settled_cutoff(asof, lag_days)

    contradictions = []
    for row in rows:
        impressions = row.get("impressions") or 0
        for field in INTERACTION_FIELDS:
            value = row.get(field) or 0
            if value > impressions:
                contradictions.append({
                    "date": str(row["date"])[:10],
                    "metric": field,
                    "value": value,
                    "impressions": impressions,
                    "why": "an interaction cannot occur without an impression, "
                           "so this day is published only in part",
                })

    trailing_zeros = []
    for row in reversed(rows):
        if (row.get("impressions") or 0) != 0:
            break
        trailing_zeros.append(str(row["date"])[:10])
    trailing_zeros.reverse()

    unsettled = [r for r in rows if _as_date(r["date"]) > cutoff]
    settled = [r for r in rows if _as_date(r["date"]) <= cutoff]

    problems = []
    if trailing_zeros:
        problems.append(
            f"{len(trailing_zeros)} trailing day(s) report zero impressions "
            f"({trailing_zeros[0]} to {trailing_zeros[-1]}); Google has most "
            f"likely not published them yet"
        )
    if contradictions:
        dates = sorted({c["date"] for c in contradictions})
        problems.append(
            f"{len(contradictions)} impossible row(s) on {', '.join(dates)}: "
            f"interactions exceed impressions, proving partial publication"
        )
    if unsettled:
        problems.append(
            f"{len(unsettled)} row(s) fall after the settled cutoff {cutoff} "
            f"and must not be reported as final"
        )

    return {
        "asof": str(_as_date(asof) if asof else datetime.date.today()),
        "settled_cutoff": str(cutoff),
        "lag_days": lag_days,
        "rows_total": len(rows),
        "rows_settled": len(settled),
        "rows_unsettled": len(unsettled),
        "trailing_zero_days": trailing_zeros,
        "contradictions": contradictions,
        "problems": problems,
        "safe_to_report": not problems,
        "settled_rows": settled,
    }


def settled_summary(series, asof=None, lag_days=SETTLE_LAG_DAYS):
    """Totals and per-day averages over the settled window only."""
    settled = inspect(series, asof, lag_days)["settled_rows"]
    if not settled:
        return {"days": 0, "note": "no settled rows in range"}

    out = {"days": len(settled),
           "from": str(settled[0]["date"])[:10],
           "to": str(settled[-1]["date"])[:10]}
    for field in ("impressions",) + INTERACTION_FIELDS:
        if any(field in r for r in settled):
            total = sum(r.get(field) or 0 for r in settled)
            out[field] = total
            out[f"{field}_per_day"] = round(total / len(settled), 2)
    return out


def main():
    parser = argparse.ArgumentParser(
        description="Guard against reporting unpublished Google Business Profile data")
    parser.add_argument("--series", help="JSON file of GBP daily rows")
    parser.add_argument("--asof", help="Treat this date as today (YYYY-MM-DD)")
    parser.add_argument("--lag-days", type=int, default=SETTLE_LAG_DAYS,
                        help=f"Days to treat as unsettled (default {SETTLE_LAG_DAYS})")
    parser.add_argument("--cutoff", action="store_true",
                        help="Print the settled cutoff date and exit")
    parser.add_argument("--trim", action="store_true",
                        help="Emit only the settled rows, as JSON")
    parser.add_argument("--json", action="store_true", help="Machine-readable output")
    args = parser.parse_args()

    if args.cutoff:
        print(settled_cutoff(args.asof, args.lag_days))
        return 0

    if not args.series:
        parser.error("--series is required unless --cutoff is given")

    with open(args.series, encoding="utf-8") as handle:
        series = json.load(handle)

    report = inspect(series, args.asof, args.lag_days)

    if args.trim:
        json.dump(report["settled_rows"], sys.stdout, indent=2)
        print()
        return 0 if report["settled_rows"] else 1

    if args.json:
        payload = dict(report)
        payload.pop("settled_rows", None)
        payload["settled_summary"] = settled_summary(series, args.asof, args.lag_days)
        json.dump(payload, sys.stdout, indent=2)
        print()
    else:
        print(f"as of {report['asof']}, settled through {report['settled_cutoff']}")
        print(f"{report['rows_settled']} settled row(s), "
              f"{report['rows_unsettled']} unsettled")
        if report["problems"]:
            print("\nDO NOT REPORT THIS RANGE AS FINAL:")
            for problem in report["problems"]:
                print(f"  - {problem}")
        else:
            print("\nsafe to report")
        summary = settled_summary(series, args.asof, args.lag_days)
        if summary.get("days"):
            print(f"\nsettled window {summary['from']} to {summary['to']} "
                  f"({summary['days']} days)")
            if "impressions_per_day" in summary:
                print(f"  impressions: {summary['impressions']} "
                      f"({summary['impressions_per_day']}/day)")

    return 0 if report["safe_to_report"] else 1


if __name__ == "__main__":
    sys.exit(main())
