"""
Regression tests for the checks that were missed on mvp1.com.au for three
consecutive weekly runs (1, 7 and 14 Sep 2026), and for the coverage gate that
exists to make sure a missed check can never again look like a passing one.

Each test below corresponds to a defect that was live on the site while the
audit reported "clean week, zero High or Critical issues".
"""

import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import audit_coverage  # noqa: E402
import site_audit  # noqa: E402


# ---------------------------------------------------------------------------
# fixture: a miniature site carrying every defect that was missed
# ---------------------------------------------------------------------------
PAGE = """<!doctype html><html><head>
<title>{title}</title>
<meta name="description" content="{desc}">
{robots}
<link rel="canonical" href="https://x.test{path}">
{ld}
</head><body>
<nav><h2>What we do</h2><a href="/">Home</a></nav>
<main><h1>Real heading</h1>{body}</main>
<footer><h2>Company</h2></footer>
</body></html>"""

GOOD_LD = '<script type="application/ld+json">{"@type":"Organization","name":"X","sameAs":["https://a"]}</script>'


def _page(path, title="A perfectly reasonable descriptive title here",
          desc="A meta description of an entirely acceptable and unremarkable length for testing.",
          robots="", body="", ld=GOOD_LD):
    return PAGE.format(title=title, desc=desc, robots=robots, path=path, ld=ld, body=body)


@pytest.fixture
def site(tmp_path):
    """Builds the exact shape of the defects found on 16 Sep 2026."""
    (tmp_path / "index.html").write_text(_page(
        "/", body='<a href="/linked">linked</a><img src="/img/logo.png" alt="Logo" width="1" height="1">'))
    (tmp_path / "linked").mkdir()
    (tmp_path / "linked" / "index.html").write_text(_page("/linked"))
    # orphan: in the sitemap, linked from nowhere
    (tmp_path / "orphan").mkdir()
    (tmp_path / "orphan" / "index.html").write_text(_page("/orphan"))
    # noindex page that is nevertheless submitted in the sitemap
    (tmp_path / "rates").mkdir()
    (tmp_path / "rates" / "index.html").write_text(
        _page("/rates", robots='<meta name="robots" content="noindex, nofollow">'))
    # brand-suffix-only title
    (tmp_path / "faq").mkdir()
    (tmp_path / "faq" / "index.html").write_text(_page("/faq", title="FAQ | X"))
    (tmp_path / "img").mkdir()
    (tmp_path / "img" / "logo.png").write_bytes(
        b"\x89PNG\r\n\x1a\n" + b"\x00" * 8 + (12).to_bytes(4, "big") + (34).to_bytes(4, "big"))

    (tmp_path / "sitemap.xml").write_text(
        "<urlset>" + "".join(
            "<url><loc>https://x.test%s</loc></url>" % p
            for p in ("/", "/linked", "/orphan", "/rates", "/faq")) + "</urlset>")
    (tmp_path / "robots.txt").write_text("User-agent: *\nAllow: /\n")
    return tmp_path


def run(root):
    pages, assets, extras = site_audit.load_from_root(str(root), "https://x.test")
    return site_audit.audit(pages, assets, extras, "https://x.test", root=str(root))


def checks_found(result):
    return {f["check"] for f in result["findings"]}


# ---------------------------------------------------------------------------
# the six defects
# ---------------------------------------------------------------------------
def test_orphan_page_is_detected(site):
    """21 real orphans went unreported for three weeks: no script built a link graph."""
    result = run(site)
    orphans = [f["url"] for f in result["findings"] if f["check"] == "link_graph.orphan_page"]
    assert "/orphan" in orphans
    assert "/linked" not in orphans


def test_noindex_url_in_sitemap_is_detected(site):
    """seo-sitemap/SKILL.md rated this High and had no code behind it."""
    result = run(site)
    hits = [f for f in result["findings"] if f["check"] == "sitemap.noindex_in_sitemap"]
    assert [f["url"] for f in hits] == ["/rates"]
    assert hits[0]["severity"] == "high"


def test_broken_asset_reference_is_detected(tmp_path):
    """The homepage served a 404 logo because markup said .jpg and the file was .png."""
    (tmp_path / "index.html").write_text(
        _page("/", body='<img src="/img/logo.jpg" alt="Logo" width="1" height="1">'))
    (tmp_path / "img").mkdir()
    (tmp_path / "img" / "logo.png").write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 16)
    result = run(tmp_path)
    assert "link_graph.broken_asset_ref" in checks_found(result)


def test_short_title_is_detected(site):
    """The length check only looked for titles that were too long."""
    result = run(site)
    short = [f["url"] for f in result["findings"] if f["check"] == "onpage.title_too_short"]
    assert "/faq" in short


def test_legacy_image_format_is_detected(site):
    """Images scored 98/100 while every raster lacked a modern alternative."""
    result = run(site)
    assert "images.legacy_format" in checks_found(result)


def test_navigation_chrome_headings_are_detected(site):
    """Eight nav/footer <h2> sat ahead of every real content heading."""
    result = run(site)
    hits = [f for f in result["findings"] if f["check"] == "onpage.chrome_heading"]
    assert hits
    labels = {entry["text"] for entry in hits[0]["labels"]}
    assert {"What we do", "Company"} <= labels


def test_pdf_links_are_not_reported_as_broken(tmp_path):
    """58 false positives on /uploads/*.pdf made the check unusable once."""
    (tmp_path / "index.html").write_text(
        _page("/", body='<a href="/uploads/doc.pdf">doc</a>'))
    (tmp_path / "uploads").mkdir()
    (tmp_path / "uploads" / "doc.pdf").write_bytes(b"%PDF-1.4")
    result = run(tmp_path)
    assert "link_graph.broken_internal_link" not in checks_found(result)


# ---------------------------------------------------------------------------
# coverage: a skipped check must never look like a passing one
# ---------------------------------------------------------------------------
def test_every_registered_check_appears_in_coverage(site):
    result = run(site)
    recorded = {c["check"] for c in result["coverage"]["checks"]}
    assert recorded == set(audit_coverage.CHECKS)


def test_ran_checks_carry_a_timestamp(site):
    result = run(site)
    for record in result["coverage"]["checks"]:
        if record["status"] == "ran":
            assert record["checked_at"], record["check"]


def test_gate_rejects_a_report_with_no_coverage_block():
    errors, _ = audit_coverage.validate({"categories": [{"name": "Images", "score": 98}]})
    assert errors and "coverage" in errors[0]


def test_gate_rejects_a_score_with_nothing_behind_it(site):
    """Images scored 98 for three weeks with no format check in existence."""
    result = run(site)
    for record in result["coverage"]["checks"]:
        if record["category"] == "Images":
            record["status"] = "skipped"
            record["reason"] = "not run"
            record["checked_at"] = None
    report = {
        "generated_at": result["generated_at"],
        "categories": [{"name": "Images", "score": 98}],
        "coverage": result["coverage"],
    }
    errors, _ = audit_coverage.validate(report, require_categories=False)
    assert any("Images" in e and "no check" in e for e in errors)


def test_gate_rejects_stale_evidence(site):
    """A 14 Sep report cited a 1 Sep crawl under a 'clean week' headline."""
    result = run(site)
    for record in result["coverage"]["checks"]:
        if record["status"] == "ran":
            record["checked_at"] = "2026-09-01T00:00:00+00:00"
    report = {
        "generated_at": "2026-09-14T00:00:00+00:00",
        "categories": [{"name": "On-Page SEO", "score": 95}],
        "coverage": result["coverage"],
    }
    errors, _ = audit_coverage.validate(report, require_categories=False)
    assert any("older than" in e for e in errors)


def test_gate_rejects_a_check_that_vanished_from_coverage(site):
    result = run(site)
    result["coverage"]["checks"] = [
        c for c in result["coverage"]["checks"]
        if c["check"] != "sitemap.noindex_in_sitemap"
    ]
    report = {"generated_at": result["generated_at"], "categories": [],
              "coverage": result["coverage"]}
    errors, _ = audit_coverage.validate(report, require_categories=False)
    assert any("sitemap.noindex_in_sitemap" in e for e in errors)


def test_unimplemented_checks_are_reported_not_hidden():
    blank = audit_coverage.template()
    statuses = {c["check"]: c["status"] for c in blank["checks"]}
    for check_id, meta in audit_coverage.CHECKS.items():
        if not meta["implemented_by"]:
            assert statuses[check_id] == "unimplemented"


# ---------------------------------------------------------------------------
# exemptions and week-over-week
# ---------------------------------------------------------------------------
def test_exemptions_are_honoured_and_kept_visible(site):
    result = run(site)
    target = next(f for f in result["findings"] if f["check"] == "images.legacy_format")
    (site / ".seo-exemptions.json").write_text(json.dumps({"exemptions": [{
        "check": "images.legacy_format",
        "url": None,
        "detail": target["src"],
        "reason": "webp encodes larger than the original",
        "since": "2026-09-16",
    }]}))
    after = run(site)
    assert target["src"] not in [f.get("src") for f in after["findings"]]
    assert any(f.get("src") == target["src"] for f in after["exempted"])


def test_compare_does_not_credit_a_finding_that_stopped_being_checked(site):
    """A finding that vanishes because nobody looked is not a fix."""
    previous = run(site)
    current = json.loads(json.dumps(previous))
    current["findings"] = [
        f for f in current["findings"] if f["check"] != "link_graph.orphan_page"
    ]
    for record in current["coverage"]["checks"]:
        if record["check"] == "link_graph.orphan_page":
            record["status"] = "skipped"
            record["reason"] = "did not run"
    diff = site_audit.compare(previous, current)
    assert diff["summary"]["cleared"] == 0
    assert diff["summary"]["cleared_unverified"] >= 1
    assert "link_graph.orphan_page" in diff["coverage_regressions"]


def test_compare_credits_a_genuine_fix(site):
    previous = run(site)
    current = json.loads(json.dumps(previous))
    current["findings"] = [
        f for f in current["findings"] if f["check"] != "link_graph.orphan_page"
    ]
    diff = site_audit.compare(previous, current)
    assert diff["summary"]["cleared"] >= 1
    assert not diff["coverage_regressions"]
