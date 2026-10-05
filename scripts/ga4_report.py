#!/usr/bin/env python3
"""
GA4 Data API v1beta - organic traffic reporting.

Queries the Google Analytics Data API for organic search traffic,
top landing pages, and session metrics with channel filtering.

Usage:
    python ga4_report.py --property 123456789
    python ga4_report.py --property 123456789 --days 90 --report top-pages
    python ga4_report.py --property 123456789 --report organic --json
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
from typing import Optional

try:
    from google.analytics.data_v1beta import BetaAnalyticsDataClient
    from google.analytics.data_v1beta.types import (
        DateRange,
        Dimension,
        Filter,
        FilterExpression,
        Metric,
        OrderBy,
        RunReportRequest,
    )
except ImportError:
    print(
        "Error: google-analytics-data required. "
        "Install with: pip install google-analytics-data",
        file=sys.stderr,
    )
    sys.exit(1)

try:
    from google_auth import get_oauth_credentials, load_config
except ImportError:
    import os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from google_auth import get_oauth_credentials, load_config

GA4_SCOPES = ["https://www.googleapis.com/auth/analytics.readonly"]


def _build_ga4_client():
    """Build the GA4 BetaAnalyticsDataClient."""
    credentials = get_oauth_credentials(GA4_SCOPES)
    if not credentials:
        return None
    try:
        return BetaAnalyticsDataClient(credentials=credentials)
    except Exception as e:
        print(f"Error building GA4 client: {e}", file=sys.stderr)
        return None


def _resolve_property(property_id: str) -> str:
    """Ensure property ID is in the correct format."""
    if not property_id:
        return ""
    if property_id.startswith("properties/"):
        return property_id
    return f"properties/{property_id}"


def organic_traffic_report(
    property_id: str,
    days: int = 28,
    limit: int = 100,
) -> dict:
    """
    Generate organic traffic report from GA4.

    Filters by sessionDefaultChannelGroup == "Organic Search" and returns
    daily sessions, top landing pages, and key metrics.

    Args:
        property_id: GA4 property ID (numeric or 'properties/123456789').
        days: Number of days to query (default: 28).
        limit: Max rows (default: 100).

    Returns:
        Dictionary with daily_data, top_pages, totals, and quota usage.
    """
    result = {
        "property": property_id,
        "report": "organic_traffic",
        "date_range": None,
        "totals": {},
        "daily_data": [],
        "top_pages": [],
        "quota_tokens_used": None,
        "error": None,
    }

    client = _build_ga4_client()
    if not client:
        result["error"] = (
            "Could not build GA4 client. Ensure the service account has "
            "Viewer access in GA4 Admin > Property Access Management."
        )
        return result

    prop = _resolve_property(property_id)
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    end_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    result["date_range"] = {"start": start_date, "end": end_date}

    # Daily organic sessions
    try:
        daily_request = RunReportRequest(
            property=prop,
            dimensions=[Dimension(name="date")],
            metrics=[
                Metric(name="sessions"),
                Metric(name="totalUsers"),
                Metric(name="screenPageViews"),
                Metric(name="bounceRate"),
                Metric(name="averageSessionDuration"),
                Metric(name="engagementRate"),
            ],
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
            dimension_filter=FilterExpression(
                filter=Filter(
                    field_name="sessionDefaultChannelGroup",
                    string_filter=Filter.StringFilter(
                        match_type=Filter.StringFilter.MatchType.EXACT,
                        value="Organic Search",
                    ),
                )
            ),
            order_bys=[OrderBy(dimension=OrderBy.DimensionOrderBy(dimension_name="date"))],
            limit=days + 5,
            return_property_quota=True,
        )

        daily_response = client.run_report(daily_request)

        for row in daily_response.rows:
            result["daily_data"].append({
                "date": row.dimension_values[0].value,
                "sessions": int(row.metric_values[0].value),
                "users": int(row.metric_values[1].value),
                "pageviews": int(row.metric_values[2].value),
                "bounce_rate": round(float(row.metric_values[3].value) * 100, 1),
                "avg_session_duration": round(float(row.metric_values[4].value), 1),
                "engagement_rate": round(float(row.metric_values[5].value) * 100, 1),
            })

        # Quota info
        if daily_response.property_quota:
            pq = daily_response.property_quota
            result["quota_tokens_used"] = {
                "daily_consumed": pq.tokens_per_day.consumed if pq.tokens_per_day else None,
                "daily_remaining": pq.tokens_per_day.remaining if pq.tokens_per_day else None,
                "hourly_consumed": pq.tokens_per_hour.consumed if pq.tokens_per_hour else None,
                "hourly_remaining": pq.tokens_per_hour.remaining if pq.tokens_per_hour else None,
            }

    except Exception as e:
        error_str = str(e)
        if "403" in error_str or "PERMISSION_DENIED" in error_str:
            result["error"] = (
                f"Permission denied for property '{property_id}'. "
                "Add the service account email as Viewer in "
                "GA4 Admin > Property Access Management."
            )
        elif "404" in error_str or "NOT_FOUND" in error_str:
            result["error"] = (
                f"Property '{property_id}' not found. "
                "Verify the numeric property ID in GA4 Admin > Property Details."
            )
        else:
            result["error"] = f"GA4 API error: {e}"
        return result

    # Top landing pages by organic sessions
    try:
        pages_request = RunReportRequest(
            property=prop,
            dimensions=[Dimension(name="landingPage")],
            metrics=[
                Metric(name="sessions"),
                Metric(name="totalUsers"),
                Metric(name="screenPageViews"),
                Metric(name="bounceRate"),
                Metric(name="engagementRate"),
            ],
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
            dimension_filter=FilterExpression(
                filter=Filter(
                    field_name="sessionDefaultChannelGroup",
                    string_filter=Filter.StringFilter(
                        match_type=Filter.StringFilter.MatchType.EXACT,
                        value="Organic Search",
                    ),
                )
            ),
            order_bys=[
                OrderBy(
                    metric=OrderBy.MetricOrderBy(metric_name="sessions"),
                    desc=True,
                )
            ],
            limit=limit,
        )

        pages_response = client.run_report(pages_request)

        for row in pages_response.rows:
            result["top_pages"].append({
                "landing_page": row.dimension_values[0].value,
                "sessions": int(row.metric_values[0].value),
                "users": int(row.metric_values[1].value),
                "pageviews": int(row.metric_values[2].value),
                "bounce_rate": round(float(row.metric_values[3].value) * 100, 1),
                "engagement_rate": round(float(row.metric_values[4].value) * 100, 1),
            })

    except Exception as e:
        # Non-fatal: daily data succeeded, pages failed
        result["pages_error"] = f"Error fetching top pages: {e}"

    # Calculate totals
    if result["daily_data"]:
        total_sessions = sum(d["sessions"] for d in result["daily_data"])
        total_users = sum(d["users"] for d in result["daily_data"])
        total_pageviews = sum(d["pageviews"] for d in result["daily_data"])
        result["totals"] = {
            "sessions": total_sessions,
            "users": total_users,
            "pageviews": total_pageviews,
            "avg_daily_sessions": round(total_sessions / len(result["daily_data"]), 1),
        }

    return result


# Hostnames GA4 may report as a session source for traffic that came from an AI
# assistant. GA4 groups many of these into an "AI Assistant" default channel
# itself; matching on the source name as well catches the ones it misses and
# keeps the report working if Google renames the channel.
AI_SOURCE_HINTS = (
    "chatgpt", "openai", "claude", "anthropic", "perplexity", "gemini",
    "copilot", "bard", "deepseek", "grok", "meta.ai", "you.com", "phind",
    "poe.com", "kagi", "mistral", "duckduckgo.com/chat", "brave.com/ai",
)


def _is_ai_row(source: str, channel: str) -> bool:
    if channel == "AI Assistant":
        return True
    src = (source or "").lower()
    return any(hint in src for hint in AI_SOURCE_HINTS)


def ai_referrals_report(property_id: str, days: int = 28, limit: int = 100) -> dict:
    """Sessions that arrived from AI assistants (ChatGPT, Claude, Perplexity...).

    Reported in EVERY audit, including when the answer is zero, because a zero
    that is not stated is indistinguishable from a check that never ran. The
    report also returns the size of the Direct bucket: AI apps that send no
    referrer land there and cannot be separated, so a low AI count is a floor,
    not a measurement of true AI-driven visits.
    """
    client = _build_ga4_client()
    if not client:
        return {"error": "Failed to build GA4 client. Check credentials."}
    prop = _resolve_property(property_id)

    def pull(start: str, end: str, dims):
        req = RunReportRequest(
            property=prop,
            date_ranges=[DateRange(start_date=start, end_date=end)],
            dimensions=[Dimension(name=d) for d in dims],
            metrics=[Metric(name="sessions"), Metric(name="engagedSessions"),
                     Metric(name="activeUsers")],
            limit=limit * 10,
        )
        resp = client.run_report(req)
        out = []
        for row in resp.rows:
            d = [v.value for v in row.dimension_values]
            m = [int(float(v.value)) for v in row.metric_values]
            out.append((d, m))
        return out

    def window(start: str, end: str) -> dict:
        rows = pull(start, end, ["sessionSource", "sessionMedium", "sessionDefaultChannelGroup", "landingPage"])
        by_source, landing, total, direct = {}, {}, 0, 0
        ai_total = ai_engaged = ai_users = 0
        for (src, med, chan, page), (sessions, engaged, users) in rows:
            total += sessions
            if chan == "Direct":
                direct += sessions
            if _is_ai_row(src, chan):
                ai_total += sessions
                ai_engaged += engaged
                ai_users += users
                key = f"{src} / {med}"
                by_source[key] = by_source.get(key, 0) + sessions
                landing[page] = landing.get(page, 0) + sessions
        return {
            "ai_sessions": ai_total,
            "ai_engaged_sessions": ai_engaged,
            "ai_users": ai_users,
            "by_source": dict(sorted(by_source.items(), key=lambda kv: -kv[1])),
            "landing_pages": dict(sorted(landing.items(), key=lambda kv: -kv[1])[:limit]),
            "all_sessions": total,
            "direct_sessions": direct,
        }

    end = datetime.now() - timedelta(days=1)
    start = end - timedelta(days=days - 1)
    prev_end = start - timedelta(days=1)
    prev_start = prev_end - timedelta(days=days - 1)
    fmt = "%Y-%m-%d"
    try:
        cur = window(start.strftime(fmt), end.strftime(fmt))
        prev = window(prev_start.strftime(fmt), prev_end.strftime(fmt))
    except Exception as e:  # noqa: BLE001 - surface the API error to the caller
        return {"error": f"GA4 API error: {e}"}

    return {
        "property": property_id,
        "date_range": {"start": start.strftime(fmt), "end": end.strftime(fmt)},
        "previous_range": {"start": prev_start.strftime(fmt), "end": prev_end.strftime(fmt)},
        "current": cur,
        "previous": prev,
        "change_sessions": cur["ai_sessions"] - prev["ai_sessions"],
        "caveat": ("AI apps that send no referrer land in Direct and cannot be "
                   "separated. Treat ai_sessions as a floor. direct_sessions shows "
                   "the size of the bucket they would be hiding in."),
    }



def top_pages_report(
    property_id: str,
    days: int = 28,
    limit: int = 50,
) -> dict:
    """
    Get top organic landing pages from GA4.

    Args:
        property_id: GA4 property ID.
        days: Number of days.
        limit: Max pages to return.

    Returns:
        Dictionary with top pages ranked by organic sessions.
    """
    report = organic_traffic_report(property_id, days, limit)
    # Slim it down to just pages
    return {
        "property": property_id,
        "report": "top_organic_pages",
        "date_range": report.get("date_range"),
        "pages": report.get("top_pages", []),
        "total_organic_sessions": report.get("totals", {}).get("sessions", 0),
        "quota_tokens_used": report.get("quota_tokens_used"),
        "error": report.get("error"),
    }


def device_breakdown(
    property_id: str,
    days: int = 28,
) -> dict:
    """
    Organic sessions broken down by device category.

    Args:
        property_id: GA4 property ID.
        days: Number of days.

    Returns:
        Dictionary with device breakdown data.
    """
    result = {"property": property_id, "report": "device_breakdown", "devices": [], "error": None}

    client = _build_ga4_client()
    if not client:
        result["error"] = "Could not build GA4 client."
        return result

    prop = _resolve_property(property_id)
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    end_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    result["date_range"] = {"start": start_date, "end": end_date}

    try:
        request = RunReportRequest(
            property=prop,
            dimensions=[Dimension(name="deviceCategory")],
            metrics=[
                Metric(name="sessions"),
                Metric(name="totalUsers"),
                Metric(name="bounceRate"),
                Metric(name="engagementRate"),
            ],
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
            dimension_filter=FilterExpression(
                filter=Filter(
                    field_name="sessionDefaultChannelGroup",
                    string_filter=Filter.StringFilter(
                        match_type=Filter.StringFilter.MatchType.EXACT,
                        value="Organic Search",
                    ),
                )
            ),
            order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="sessions"), desc=True)],
        )
        response = client.run_report(request)
        for row in response.rows:
            result["devices"].append({
                "category": row.dimension_values[0].value,
                "sessions": int(row.metric_values[0].value),
                "users": int(row.metric_values[1].value),
                "bounce_rate": round(float(row.metric_values[2].value) * 100, 1),
                "engagement_rate": round(float(row.metric_values[3].value) * 100, 1),
            })
    except Exception as e:
        result["error"] = f"GA4 device breakdown error: {e}"

    return result


def country_breakdown(
    property_id: str,
    days: int = 28,
    limit: int = 20,
) -> dict:
    """
    Organic sessions broken down by country.

    Args:
        property_id: GA4 property ID.
        days: Number of days.
        limit: Max countries to return.

    Returns:
        Dictionary with country breakdown data.
    """
    result = {"property": property_id, "report": "country_breakdown", "countries": [], "error": None}

    client = _build_ga4_client()
    if not client:
        result["error"] = "Could not build GA4 client."
        return result

    prop = _resolve_property(property_id)
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    end_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    result["date_range"] = {"start": start_date, "end": end_date}

    try:
        request = RunReportRequest(
            property=prop,
            dimensions=[Dimension(name="country")],
            metrics=[
                Metric(name="sessions"),
                Metric(name="totalUsers"),
            ],
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
            dimension_filter=FilterExpression(
                filter=Filter(
                    field_name="sessionDefaultChannelGroup",
                    string_filter=Filter.StringFilter(
                        match_type=Filter.StringFilter.MatchType.EXACT,
                        value="Organic Search",
                    ),
                )
            ),
            order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="sessions"), desc=True)],
            limit=limit,
        )
        response = client.run_report(request)
        for row in response.rows:
            result["countries"].append({
                "country": row.dimension_values[0].value,
                "sessions": int(row.metric_values[0].value),
                "users": int(row.metric_values[1].value),
            })
    except Exception as e:
        result["error"] = f"GA4 country breakdown error: {e}"

    return result


def main():
    parser = argparse.ArgumentParser(
        description="GA4 Data API - organic traffic reporting"
    )
    parser.add_argument(
        "--property", "-p",
        help="GA4 property ID (numeric, e.g., 123456789). Uses config default if not specified.",
    )
    parser.add_argument("--days", "-d", type=int, default=28, help="Number of days (default: 28)")
    parser.add_argument(
        "--report", "-r",
        choices=["organic", "top-pages", "device", "country", "ai-referrals"],
        default="organic",
        help="Report type (default: organic)",
    )
    parser.add_argument("--limit", type=int, default=50, help="Max rows (default: 50)")
    parser.add_argument("--json", "-j", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    # Resolve property
    prop = args.property
    if not prop:
        config = load_config()
        prop = config.get("ga4_property_id") or ""
        # Strip 'properties/' prefix if present for consistency
        if prop and prop.startswith("properties/"):
            prop = prop[len("properties/"):]
    if not prop:
        print(
            "Error: No GA4 property specified. Use --property or set ga4_property_id in config.",
            file=sys.stderr,
        )
        sys.exit(1)

    if args.report == "top-pages":
        result = top_pages_report(prop, args.days, args.limit)
    elif args.report == "device":
        result = device_breakdown(prop, args.days)
    elif args.report == "country":
        result = country_breakdown(prop, args.days, args.limit)
    elif args.report == "ai-referrals":
        result = ai_referrals_report(prop, args.days, args.limit)
    else:
        result = organic_traffic_report(prop, args.days, args.limit)

    if result.get("error"):
        print(f"Error: {result['error']}", file=sys.stderr)
        if not args.json:
            sys.exit(1)

    if args.json:
        print(json.dumps(result, indent=2, default=str))
    elif args.report == "ai-referrals" and not result.get("error"):
        cur, prev = result["current"], result["previous"]
        print("=== AI Assistant Referrals ===")
        print(f"Period: {result['date_range']['start']} to {result['date_range']['end']}"
              f" (previous {result['previous_range']['start']} to {result['previous_range']['end']})")
        print(f"AI sessions: {cur['ai_sessions']} (previous {prev['ai_sessions']}, "
              f"change {result['change_sessions']:+d}) | engaged {cur['ai_engaged_sessions']}")
        for src, n in cur["by_source"].items():
            print(f"  {src}: {n}")
        for page, n in cur["landing_pages"].items():
            print(f"  lands on {page}: {n}")
        print(f"Direct sessions (where referrer-less AI visits hide): {cur['direct_sessions']} of {cur['all_sessions']}")
        print(result["caveat"])
    else:
        if args.report == "top-pages":
            print(f"=== Top Organic Landing Pages ===")
            print(f"Property: {prop} | Period: {result.get('date_range', {}).get('start')} to {result.get('date_range', {}).get('end')}")
            print(f"Total organic sessions: {result.get('total_organic_sessions', 0):,}")
            print()
            for i, page in enumerate(result.get("pages", [])[:20], 1):
                print(f"  {i:2d}. {page['landing_page']}")
                print(f"      Sessions: {page['sessions']:,} | Users: {page['users']:,} | Bounce: {page['bounce_rate']}%")
        else:
            totals = result.get("totals", {})
            print(f"=== GA4 Organic Traffic Report ===")
            print(f"Property: {prop}")
            dr = result.get("date_range", {})
            print(f"Period: {dr.get('start')} to {dr.get('end')}")
            print(f"\nSessions: {totals.get('sessions', 0):,} | Users: {totals.get('users', 0):,} | Pageviews: {totals.get('pageviews', 0):,}")
            print(f"Avg Daily Sessions: {totals.get('avg_daily_sessions', 0):,.0f}")

            quota = result.get("quota_tokens_used")
            if quota and quota.get("daily_remaining") is not None:
                print(f"\nQuota: {quota['daily_consumed']} tokens used / {quota['daily_remaining']} remaining (daily)")

            pages = result.get("top_pages", [])
            if pages:
                print(f"\nTop {min(10, len(pages))} Organic Landing Pages:")
                for i, page in enumerate(pages[:10], 1):
                    print(f"  {i:2d}. {page['landing_page']} ({page['sessions']:,} sessions)")


if __name__ == "__main__":
    main()
