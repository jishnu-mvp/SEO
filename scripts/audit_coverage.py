#!/usr/bin/env python3
"""
Audit coverage registry, manifest and gate for Claude SEO.

This exists because of a specific, documented failure. Between 1 and 14 Sep
2026 the weekly audit of mvp1.com.au reported "clean week, zero High or
Critical issues" three times while six real defects sat on the live site --
21 orphaned pages, a noindexed URL submitted in the sitemap, 32 legacy-format
images, four brand-suffix-only titles, eight navigation headings ahead of
every page's content outline, and a homepage image returning 404.

Every one of those was covered by a rule the repo already contained. None of
those rules were code. The audit's real coverage was bounded by what the
Python scripts emitted, not by what the SKILL.md files instructed, and the
report format had no field in which to say "this was not checked". A category
with zero findings was indistinguishable from a category nobody examined.

This module closes that hole three ways:

1. CHECKS is the single source of truth for what a full audit claims to do.
   A check with ``implemented_by=None`` is a known gap and is reported as
   ``unimplemented`` on every run -- loudly, in the report, forever, until
   someone writes it. Gaps cannot go quiet again.

2. Every audit writes a ``coverage`` block recording, per check: whether it
   ran, how many pages it saw, when the evidence was gathered, and why it was
   skipped if it was. Carried-forward evidence keeps its original timestamp.

3. ``--validate`` is a gate. It fails the run when a category reports a score
   without any check behind it, when evidence is older than the report claims,
   or when a required check silently vanished. Wire it in before the report is
   written, not after.

Usage:
    python audit_coverage.py --list                      # the registry
    python audit_coverage.py --gaps                      # unimplemented only
    python audit_coverage.py --template > coverage.json  # blank manifest
    python audit_coverage.py --validate audit-data.json [--max-age-days 2]
    python audit_coverage.py --merge audit-data.json --coverage coverage.json

Exit codes: 0 = pass, 1 = validation failures, 2 = bad input.
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))

# Categories a full audit must attempt. Mirrors the audit-data.json contract in
# skills/seo-audit/SKILL.md. "Authority / Backlinks" is included deliberately:
# it was absent from every mvp1.com.au snapshot, so the site went three weeks
# with no link measurement at all and nothing recorded that as a gap.
CATEGORIES = [
    "Technical SEO",
    "On-Page SEO",
    "Schema / Structured Data",
    "Images",
    "AI Search Readiness (GEO / AEO)",
    "Performance (Core Web Vitals)",
    "Local SEO / Google Business Profile",
    "Content Quality",
    "Authority / Backlinks",
]

# fix_class semantics:
#   "technical" -- not rendered as reader-facing copy. Safe to fix and ship
#                  without approval under the mvp1-website standing rule.
#   "content"   -- changes what a visitor reads or sees. Always needs approval.
#   "external"  -- lives outside the repo (GBP, Search Console, DNS).
#   None        -- diagnostic only, nothing to fix.
CHECKS = {
    # -- Technical and crawl ------------------------------------------------
    "link_graph.orphan_page": {
        "category": "Technical SEO",
        "title": "Page has no inbound internal link",
        "severity": "medium",
        "implemented_by": "site_audit.py",
        "fix_class": "technical",
        "autofix": None,  # needs a site-specific listing/hub, not mechanical
        "note": "Counted from the SERVED html only. A list built at runtime by "
                "JavaScript leaves no link for a non-rendering crawler.",
    },
    "link_graph.broken_internal_link": {
        "category": "Technical SEO",
        "title": "Internal link points at a missing page",
        "severity": "high",
        "implemented_by": "site_audit.py",
        "fix_class": "technical",
        "autofix": "site_autofix.py",
    },
    "link_graph.broken_asset_ref": {
        "category": "Technical SEO",
        "title": "Image, script or stylesheet reference is missing",
        "severity": "high",
        "implemented_by": "site_audit.py",
        "fix_class": "technical",
        "autofix": "site_autofix.py",
    },
    "sitemap.noindex_in_sitemap": {
        "category": "Technical SEO",
        "title": "Sitemap submits a URL that is noindexed",
        "severity": "high",
        "implemented_by": "site_audit.py",
        "fix_class": "technical",
        "autofix": "site_autofix.py",
    },
    "sitemap.missing_from_sitemap": {
        "category": "Technical SEO",
        "title": "Indexable, internally linked page is absent from the sitemap",
        "severity": "medium",
        "implemented_by": "site_audit.py",
        "fix_class": "technical",
        "autofix": "site_autofix.py",
    },
    "sitemap.url_unreachable": {
        "category": "Technical SEO",
        "title": "Sitemap URL does not resolve to a page",
        "severity": "high",
        "implemented_by": "site_audit.py",
        "fix_class": "technical",
        "autofix": None,
    },
    "crawl.coverage_shortfall": {
        "category": "Technical SEO",
        "title": "Audit read fewer pages than the site declares",
        "severity": "high",
        "implemented_by": "site_audit.py",
        "fix_class": None,
        "autofix": None,
        "note": "Scoring a site you did not finish reading is the failure this "
                "whole module exists to prevent.",
    },
    "indexability.noindex": {
        "category": "Technical SEO",
        "title": "Page is excluded from indexing",
        "severity": "info",
        "implemented_by": "site_audit.py",
        "fix_class": None,
        "autofix": None,
    },
    # -- On-page ------------------------------------------------------------
    "onpage.title_too_short": {
        "category": "On-Page SEO",
        "title": "Title is too short to describe the page",
        "severity": "low",
        "implemented_by": "site_audit.py",
        "fix_class": "technical",
        "autofix": None,  # needs language; the agent writes it, see --propose
    },
    "onpage.title_too_long": {
        "category": "On-Page SEO",
        "title": "Title exceeds the search display limit",
        "severity": "low",
        "implemented_by": "site_audit.py",
        "fix_class": "technical",
        "autofix": None,
    },
    "onpage.meta_description_too_short": {
        "category": "On-Page SEO",
        "title": "Meta description is too short",
        "severity": "low",
        "implemented_by": "site_audit.py",
        "fix_class": "technical",
        "autofix": None,
    },
    "onpage.meta_description_too_long": {
        "category": "On-Page SEO",
        "title": "Meta description exceeds the display limit",
        "severity": "low",
        "implemented_by": "site_audit.py",
        "fix_class": "technical",
        "autofix": None,
    },
    "onpage.h1_missing": {
        "category": "On-Page SEO",
        "title": "Page has no H1",
        "severity": "medium",
        "implemented_by": "site_audit.py",
        "fix_class": "content",
        "autofix": None,
    },
    "onpage.h1_multiple": {
        "category": "On-Page SEO",
        "title": "Page has more than one H1",
        "severity": "low",
        "implemented_by": "site_audit.py",
        "fix_class": "content",
        "autofix": None,
    },
    "onpage.chrome_heading": {
        "category": "On-Page SEO",
        "title": "Navigation or footer label is marked up as a heading",
        "severity": "low",
        "implemented_by": "site_audit.py",
        "fix_class": "technical",
        "autofix": "site_autofix.py",
        "note": "Same words, same styling -- only the tag changes, so this is "
                "not a content edit. It pushes real content headings down the "
                "outline and derails heading-based extraction by answer engines.",
    },
    "onpage.heading_level_skip": {
        "category": "On-Page SEO",
        "title": "Heading outline skips a level",
        "severity": "low",
        "implemented_by": "site_audit.py",
        "fix_class": "technical",
        "autofix": None,
    },
    "onpage.canonical_missing": {
        "category": "On-Page SEO",
        "title": "Page has no canonical link",
        "severity": "medium",
        "implemented_by": "site_audit.py",
        "fix_class": "technical",
        "autofix": None,
    },
    # -- Images -------------------------------------------------------------
    "images.legacy_format": {
        "category": "Images",
        "title": "Raster image is served without a modern format",
        "severity": "low",
        "implemented_by": "site_audit.py",
        "fix_class": "technical",
        "autofix": "site_autofix.py",
    },
    "images.missing_alt": {
        "category": "Images",
        "title": "Image has no alt attribute",
        "severity": "medium",
        "implemented_by": "site_audit.py",
        "fix_class": "content",
        "autofix": None,
    },
    "images.missing_dimensions": {
        "category": "Images",
        "title": "Image has no width/height, risking layout shift",
        "severity": "low",
        "implemented_by": "site_audit.py",
        "fix_class": "technical",
        "autofix": "site_autofix.py",
    },
    "images.oversized": {
        "category": "Images",
        "title": "Image file is larger than its role warrants",
        "severity": "low",
        "implemented_by": "site_audit.py",
        "fix_class": "technical",
        "autofix": None,
    },
    # -- Schema -------------------------------------------------------------
    "schema.invalid_json": {
        "category": "Schema / Structured Data",
        "title": "JSON-LD block does not parse",
        "severity": "high",
        "implemented_by": "site_audit.py",
        "fix_class": "technical",
        "autofix": None,
    },
    "schema.missing_on_page": {
        "category": "Schema / Structured Data",
        "title": "Page carries no structured data at all",
        "severity": "low",
        "implemented_by": "site_audit.py",
        "fix_class": "technical",
        "autofix": None,
    },
    # -- AEO / GEO ----------------------------------------------------------
    "aeo.llms_txt_missing": {
        "category": "AI Search Readiness (GEO / AEO)",
        "title": "No llms.txt at the site root",
        "severity": "low",
        "implemented_by": "site_audit.py",
        "fix_class": "technical",
        "autofix": None,
    },
    "aeo.ai_crawler_blocked": {
        "category": "AI Search Readiness (GEO / AEO)",
        "title": "robots.txt blocks an answer-engine crawler",
        "severity": "high",
        "implemented_by": "site_audit.py",
        "fix_class": "technical",
        "autofix": None,
    },
    "aeo.qa_page_without_faq_schema": {
        "category": "AI Search Readiness (GEO / AEO)",
        "title": "Page asks questions in headings but has no FAQPage schema",
        "severity": "low",
        "implemented_by": "site_audit.py",
        "fix_class": "content",
        "autofix": None,
        "note": "Content-class on purpose. FAQ markup must match visible Q&A, so "
                "shipping empty or invisible-only FAQPage is worse than nothing.",
    },
    "geo.entity_missing": {
        "category": "AI Search Readiness (GEO / AEO)",
        "title": "No Organization or LocalBusiness entity found site-wide",
        "severity": "high",
        "implemented_by": "site_audit.py",
        "fix_class": "technical",
        "autofix": None,
    },
    "geo.sameas_missing": {
        "category": "AI Search Readiness (GEO / AEO)",
        "title": "Entity has no sameAs profile links",
        "severity": "medium",
        "implemented_by": "site_audit.py",
        "fix_class": "technical",
        "autofix": None,
    },
    # -- Categories that still depend on credentials or on judgement --------
    "performance.lab": {
        "category": "Performance (Core Web Vitals)",
        "title": "Lab performance measured (Lighthouse / PSI)",
        "severity": "info",
        "implemented_by": "pagespeed_check.py",
        "fix_class": None,
        "autofix": None,
    },
    "performance.field": {
        "category": "Performance (Core Web Vitals)",
        "title": "Field performance measured (CrUX)",
        "severity": "info",
        "implemented_by": "crux_history.py",
        "fix_class": None,
        "autofix": None,
    },
    "content.quality_score": {
        "category": "Content Quality",
        "title": "QRG-aligned content quality scored per page",
        "severity": "info",
        "implemented_by": "content_quality.py",
        "fix_class": None,
        "autofix": None,
    },
    "local.gbp_state": {
        "category": "Local SEO / Google Business Profile",
        "title": "Google Business Profile state read live",
        "severity": "info",
        "implemented_by": None,
        "fix_class": "external",
        "autofix": None,
        "note": "No first-party script. Runs through a connector (Windsor.ai) "
                "when one is attached; otherwise this reports as skipped with a "
                "reason rather than silently carrying last week's numbers.",
    },
    "authority.referring_domains": {
        "category": "Authority / Backlinks",
        "title": "Referring domains measured",
        "severity": "info",
        "implemented_by": "moz_api.py",
        "fix_class": None,
        "autofix": None,
    },
    "authority.link_verification": {
        "category": "Authority / Backlinks",
        "title": "Claimed backlinks DOM-verified",
        "severity": "info",
        "implemented_by": "verify_backlinks.py",
        "fix_class": None,
        "autofix": None,
    },
}

VALID_STATUS = {"ran", "skipped", "unimplemented", "carried_forward"}


# ---------------------------------------------------------------------------
# Registry helpers
# ---------------------------------------------------------------------------
def checks_for(category):
    return {k: v for k, v in CHECKS.items() if v["category"] == category}


def gaps():
    """Checks the repo claims but has no code for."""
    return {k: v for k, v in CHECKS.items() if not v["implemented_by"]}


def autofixable():
    return {k: v for k, v in CHECKS.items() if v.get("autofix")}


def template():
    """A blank manifest with every check pre-listed, so none can be forgotten."""
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    records = []
    for check_id, meta in CHECKS.items():
        records.append({
            "check": check_id,
            "category": meta["category"],
            "status": "unimplemented" if not meta["implemented_by"] else "skipped",
            "reason": "no implementation in this repo" if not meta["implemented_by"]
                      else "not yet run",
            "pages_checked": 0,
            "findings": 0,
            "checked_at": None,
            "implemented_by": meta["implemented_by"],
        })
    return {"generated_at": now, "checks": records}


# ---------------------------------------------------------------------------
# Validation -- the gate
# ---------------------------------------------------------------------------
def _parse_ts(value):
    if not value:
        return None
    try:
        text = value.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(text)
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def validate(report, max_age_days=2, require_categories=True):
    """
    Check an audit-data.json envelope for coverage honesty.

    Returns (errors, warnings). Errors fail the run.
    """
    errors, warnings = [], []

    coverage = report.get("coverage")
    if not coverage or not coverage.get("checks"):
        errors.append(
            "no coverage block: the report cannot say which checks ran, so a "
            "skipped check is indistinguishable from a passing one. Run "
            "site_audit.py and merge its coverage before reporting."
        )
        return errors, warnings

    records = {c.get("check"): c for c in coverage["checks"] if c.get("check")}

    for check_id, rec in records.items():
        if check_id not in CHECKS:
            warnings.append("coverage names an unknown check: %s" % check_id)
        status = rec.get("status")
        if status not in VALID_STATUS:
            errors.append("%s has invalid status %r" % (check_id, status))
        if status in ("skipped", "unimplemented") and not rec.get("reason"):
            errors.append("%s is %s with no reason given" % (check_id, status))

    # Every registered check must appear. A check that vanishes from the
    # manifest is exactly how the sitemap rule went quiet for three weeks.
    for check_id in CHECKS:
        if check_id not in records:
            errors.append(
                "%s is in the registry but absent from this run's coverage" % check_id
            )

    # A category cannot carry a score with nothing behind it.
    report_ts = _parse_ts(report.get("generated_at")) or datetime.now(timezone.utc)
    stale_before = report_ts - timedelta(days=max_age_days)

    categories = {c.get("name"): c for c in report.get("categories", []) if c.get("name")}
    if require_categories:
        for name in CATEGORIES:
            if name not in categories:
                warnings.append("category not present in this report: %s" % name)

    for name, cat in categories.items():
        ran = [
            r for cid, r in records.items()
            if CHECKS.get(cid, {}).get("category") == name and r.get("status") == "ran"
        ]
        has_score = cat.get("score") is not None
        if has_score and not ran:
            errors.append(
                "category %r reports score %s but no check in it actually ran. "
                "Either run one, or drop the score and report the category as "
                "unmeasured." % (name, cat.get("score"))
            )
        for rec in ran:
            ts = _parse_ts(rec.get("checked_at"))
            if ts is None:
                errors.append(
                    "%s claims to have run but carries no checked_at timestamp"
                    % rec["check"]
                )
            elif ts < stale_before:
                errors.append(
                    "%s presents evidence gathered %s as part of a %s report "
                    "(older than %d day(s)). Re-run it or mark it carried_forward."
                    % (rec["check"], ts.date().isoformat(),
                       report_ts.date().isoformat(), max_age_days)
                )

    for cid, rec in records.items():
        if rec.get("status") == "carried_forward":
            ts = _parse_ts(rec.get("checked_at"))
            warnings.append(
                "%s is carried forward from %s -- say so in the report text, do "
                "not present it as this week's measurement"
                % (cid, ts.date().isoformat() if ts else "an unknown date")
            )

    open_gaps = [cid for cid, r in records.items() if r.get("status") == "unimplemented"]
    if open_gaps:
        warnings.append(
            "%d check(s) have no implementation and were not performed: %s"
            % (len(open_gaps), ", ".join(sorted(open_gaps)))
        )

    return errors, warnings


def merge(report, coverage):
    """Attach a coverage manifest to an audit-data.json envelope."""
    report["coverage"] = coverage
    report.setdefault(
        "generated_at",
        datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    )
    return report


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Audit coverage registry, manifest and validation gate.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--list", action="store_true", help="print the check registry")
    group.add_argument("--gaps", action="store_true", help="print unimplemented checks")
    group.add_argument("--template", action="store_true", help="print a blank manifest")
    group.add_argument("--validate", metavar="AUDIT_JSON", help="gate an audit-data.json")
    group.add_argument("--merge", metavar="AUDIT_JSON", help="attach a coverage manifest")
    parser.add_argument("--coverage", metavar="JSON", help="coverage file for --merge")
    parser.add_argument("--max-age-days", type=int, default=2,
                        help="how old evidence may be before it is stale (default 2)")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    parser.add_argument("--output", metavar="PATH", help="write --merge result here")
    args = parser.parse_args()

    if args.list:
        if args.json:
            print(json.dumps(CHECKS, indent=2))
        else:
            for category in CATEGORIES:
                items = checks_for(category)
                print("\n%s  (%d checks)" % (category, len(items)))
                for cid, meta in sorted(items.items()):
                    mark = "  " if meta["implemented_by"] else "! "
                    print("  %s%-42s %-8s %-10s %s" % (
                        mark, cid, meta["severity"],
                        meta.get("fix_class") or "-",
                        meta["implemented_by"] or "NO IMPLEMENTATION"))
            print("\n! = known gap, reported as unimplemented on every run")
        return 0

    if args.gaps:
        found = gaps()
        if args.json:
            print(json.dumps(found, indent=2))
        else:
            if not found:
                print("No gaps: every registered check has an implementation.")
            for cid, meta in sorted(found.items()):
                print("%-42s %s" % (cid, meta["category"]))
                if meta.get("note"):
                    print("    %s" % meta["note"])
        return 0

    if args.template:
        print(json.dumps(template(), indent=2))
        return 0

    if args.merge:
        if not args.coverage:
            print("--merge requires --coverage", file=sys.stderr)
            return 2
        report = json.load(open(args.merge, encoding="utf-8"))
        cov = json.load(open(args.coverage, encoding="utf-8"))
        cov = cov.get("coverage", cov)
        merged = merge(report, cov)
        out = args.output or args.merge
        with open(out, "w", encoding="utf-8") as handle:
            json.dump(merged, handle, indent=2)
        print("coverage merged into %s (%d check records)"
              % (out, len(cov.get("checks", []))))
        return 0

    # --validate
    try:
        report = json.load(open(args.validate, encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print("cannot read %s: %s" % (args.validate, exc), file=sys.stderr)
        return 2

    errors, warnings = validate(report, max_age_days=args.max_age_days)

    if args.json:
        print(json.dumps({
            "status": "PASS" if not errors else "FAIL",
            "errors": errors,
            "warnings": warnings,
        }, indent=2))
    else:
        for warning in warnings:
            print("WARN  %s" % warning)
        for error in errors:
            print("FAIL  %s" % error)
        print("\n%s -- %d error(s), %d warning(s)"
              % ("PASS" if not errors else "FAIL", len(errors), len(warnings)))
        if errors:
            print("\nDo not present this report. Fix the coverage, then re-run.")

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
