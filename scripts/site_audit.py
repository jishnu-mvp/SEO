#!/usr/bin/env python3
"""
Deterministic site-wide SEO/AEO/GEO checks for Claude SEO.

Implements the checks that existed only as prose in SKILL.md files and were
therefore never performed. Between 1 and 14 Sep 2026 the weekly audit of
mvp1.com.au missed six real defects this script finds in one pass:

  * 21 pages with no inbound internal link, because three hub pages built
    their lists at runtime and served an empty container
  * a noindexed URL submitted in sitemap.xml (a documented High-severity rule
    in seo-sitemap/SKILL.md that had no code behind it)
  * a homepage image reference returning 404
  * 32 raster images with no WebP/AVIF alternative
  * four brand-suffix-only titles, because the length check was written in one
    direction only
  * eight navigation labels marked up as <h2>, ahead of every real heading

Deliberately stdlib-only. A check that must never be silently skipped cannot
depend on an optional package being importable -- that is the same class of
failure it exists to catch. Network mode imports requests lazily; --root mode
needs nothing at all.

Two modes:

    --root DIR    read a static site from disk (fast, exact, pre-deploy)
    --url URL     crawl a live site through the SSRF-safe fetcher

Usage:
    python site_audit.py --root ../mvp1-website --base-url https://mvp1.com.au
    python site_audit.py --url https://example.com --max-pages 200
    python site_audit.py --root . --base-url https://x.com --json > audit.json
    python site_audit.py --root . --base-url https://x.com --fail-on high

Output: JSON with `findings`, `coverage` (an audit_coverage manifest), `stats`
and `pages`. Exit 0 unless --fail-on is set and a finding meets that severity.
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse, urlunparse

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPTS_DIR)

from audit_coverage import CHECKS  # noqa: E402

# Thresholds. Symmetric on purpose: the mvp1.com.au title check only ever
# looked for titles that were too long, so four that were far too short were
# invisible for three weeks.
TITLE_MIN, TITLE_MAX = 30, 60
DESC_MIN, DESC_MAX = 70, 155
IMAGE_WARN_BYTES = 200 * 1024
IMAGE_FAIL_BYTES = 500 * 1024
MODERN_FORMATS = (".webp", ".avif")
RASTER_FORMATS = (".png", ".jpg", ".jpeg", ".gif")
LANDMARKS = ("nav", "header", "footer")

# Answer-engine crawlers worth checking individually in robots.txt.
AI_AGENTS = [
    "GPTBot", "OAI-SearchBot", "ChatGPT-User", "ClaudeBot", "Claude-User",
    "PerplexityBot", "Google-Extended", "Applebot-Extended", "Bytespider",
    "meta-externalagent", "CCBot", "Amazonbot",
]


# ---------------------------------------------------------------------------
# Tolerant HTML extraction
# ---------------------------------------------------------------------------
class PageParser(HTMLParser):
    """Pulls the SEO-relevant shape out of a page, tracking landmark context."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title = None
        self.meta = {}
        self.canonical = None
        self.links = []          # (href, in_landmark)
        self.images = []         # dict per <img>
        self.headings = []       # (level, text, in_landmark)
        self.jsonld = []
        self.picture_sources = []
        self._stack = []
        self._in_title = False
        self._in_script_ld = False
        self._script_buf = []
        self._heading = None
        self._heading_buf = []

    # -- helpers
    def _landmark(self):
        return next((t for t in reversed(self._stack) if t in LANDMARKS), None)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self._stack.append(tag)

        if tag == "title":
            self._in_title = True
        elif tag == "meta":
            name = (attrs.get("name") or attrs.get("property") or "").lower()
            if name:
                self.meta[name] = attrs.get("content", "")
        elif tag == "link" and (attrs.get("rel") or "").lower() == "canonical":
            self.canonical = attrs.get("href")
        elif tag == "a" and attrs.get("href"):
            self.links.append((attrs["href"], self._landmark()))
        elif tag == "img":
            self.images.append({
                "src": attrs.get("src"),
                "alt": attrs.get("alt"),
                "width": attrs.get("width"),
                "height": attrs.get("height"),
                "loading": attrs.get("loading"),
                "in_picture": "picture" in self._stack,
            })
        elif tag == "source" and attrs.get("srcset"):
            self.picture_sources.append(attrs["srcset"])
        elif tag == "script":
            if (attrs.get("type") or "").lower() == "application/ld+json":
                self._in_script_ld = True
                self._script_buf = []
            elif attrs.get("src"):
                self.links.append((attrs["src"], "__asset__"))
        elif tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self._heading = (int(tag[1]), self._landmark())
            self._heading_buf = []

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if self._stack and self._stack[-1] == tag:
            self._stack.pop()
        if tag == "title":
            self._in_title = False

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        elif tag == "script" and self._in_script_ld:
            self._in_script_ld = False
            self.jsonld.append("".join(self._script_buf))
        elif tag in ("h1", "h2", "h3", "h4", "h5", "h6") and self._heading:
            level, landmark = self._heading
            text = re.sub(r"\s+", " ", "".join(self._heading_buf)).strip()
            if text:
                self.headings.append((level, text, landmark))
            self._heading = None
        for i in range(len(self._stack) - 1, -1, -1):
            if self._stack[i] == tag:
                del self._stack[i:]
                break

    def handle_data(self, data):
        if self._in_title:
            self.title = ((self.title or "") + data)
        if self._in_script_ld:
            self._script_buf.append(data)
        if self._heading is not None:
            self._heading_buf.append(data)


def parse_page(html):
    parser = PageParser()
    try:
        parser.feed(html)
    except Exception:  # malformed markup must not abort the whole audit
        pass
    return parser


# ---------------------------------------------------------------------------
# Image dimensions and weight, without Pillow
# ---------------------------------------------------------------------------
def image_dimensions(path):
    """Read intrinsic size from the file header. Returns (w, h) or None."""
    try:
        with open(path, "rb") as handle:
            head = handle.read(32)
            if head[:8] == b"\x89PNG\r\n\x1a\n":
                return (int.from_bytes(head[16:20], "big"),
                        int.from_bytes(head[20:24], "big"))
            if head[:3] == b"GIF":
                return (int.from_bytes(head[6:8], "little"),
                        int.from_bytes(head[8:10], "little"))
            if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
                handle.seek(0)
                blob = handle.read(64)
                if blob[12:16] == b"VP8X":
                    w = int.from_bytes(blob[24:27], "little") + 1
                    h = int.from_bytes(blob[27:30], "little") + 1
                    return (w, h)
                return None
            if head[:2] == b"\xff\xd8":  # JPEG: walk the segment chain
                handle.seek(2)
                while True:
                    marker = handle.read(2)
                    if len(marker) < 2 or marker[0] != 0xFF:
                        return None
                    if 0xC0 <= marker[1] <= 0xCF and marker[1] not in (0xC4, 0xC8, 0xCC):
                        handle.read(3)
                        block = handle.read(4)
                        return (int.from_bytes(block[2:4], "big"),
                                int.from_bytes(block[0:2], "big"))
                    size = int.from_bytes(handle.read(2), "big")
                    if size < 2:
                        return None
                    handle.seek(size - 2, 1)
    except OSError:
        return None
    return None


# ---------------------------------------------------------------------------
# Source loading
# ---------------------------------------------------------------------------
def _norm_path(path):
    """/a/b/index.html and /a/b/ both normalise to /a/b."""
    path = path.split("#")[0].split("?")[0]
    if path.endswith("/index.html"):
        path = path[: -len("index.html")]
    if len(path) > 1 and path.endswith("/"):
        path = path[:-1]
    return path or "/"


def load_from_root(root, base_url):
    """Read a static site from disk. Returns (pages, assets, extras)."""
    pages, assets = {}, set()
    skip_dirs = {".git", "node_modules", ".audit-history", "scripts", ".well-known"}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in skip_dirs and not d.startswith(".")]
        for name in filenames:
            full = os.path.join(dirpath, name)
            rel = "/" + os.path.relpath(full, root).replace(os.sep, "/")
            if name.endswith(".html"):
                try:
                    html = open(full, encoding="utf-8", errors="replace").read()
                except OSError:
                    continue
                pages[_norm_path(rel)] = {"html": html, "file": full, "rel": rel}
            else:
                assets.add(rel)

    extras = {}
    for special in ("sitemap.xml", "robots.txt", "llms.txt"):
        path = os.path.join(root, special)
        if os.path.exists(path):
            extras[special] = open(path, encoding="utf-8", errors="replace").read()
    return pages, assets, extras


def load_from_url(base_url, max_pages, timeout):
    """Crawl a live site through the SSRF-safe fetcher."""
    from url_safety import safe_requests_get  # lazy: --root needs no deps

    origin = "{0}://{1}".format(*urlparse(base_url)[:2])
    pages, assets, extras = {}, set(), {}

    for special in ("sitemap.xml", "robots.txt", "llms.txt"):
        try:
            resp = safe_requests_get(urljoin(origin + "/", special), timeout=timeout)
            if resp.status_code == 200:
                extras[special] = resp.text
        except Exception:
            pass

    seeds = [_norm_path(urlparse(u).path) for u in sitemap_urls(extras.get("sitemap.xml", ""))]
    queue = ["/"] + [s for s in seeds if s != "/"]
    seen = set()
    truncated = False

    while queue:
        if len(pages) >= max_pages:
            truncated = True
            break
        path = queue.pop(0)
        if path in seen:
            continue
        seen.add(path)
        try:
            resp = safe_requests_get(origin + path, timeout=timeout)
        except Exception:
            continue
        if resp.status_code != 200 or "html" not in resp.headers.get("content-type", ""):
            if resp.status_code != 200:
                pages[path] = {"html": "", "status": resp.status_code, "rel": path}
            continue
        pages[path] = {"html": resp.text, "status": 200, "rel": path}
        for href, _ in parse_page(resp.text).links:
            target = resolve_internal(href, path, origin)
            if target and target not in seen and target not in queue:
                queue.append(target)

    extras["__truncated__"] = truncated
    extras["__queued__"] = len(queue)
    return pages, assets, extras


def resolve_internal(href, from_path, origin):
    """Return the normalised internal path for href, or None if external."""
    if not href or href.startswith(("#", "mailto:", "tel:", "javascript:", "data:")):
        return None
    absolute = urljoin(origin + from_path, href)
    parsed = urlparse(absolute)
    if urlparse(origin).netloc and parsed.netloc != urlparse(origin).netloc:
        return None
    return _norm_path(parsed.path)


def sitemap_urls(xml):
    return re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", xml or "")


def _target_exists(target, root, assets):
    """
    Is this internal path a real file rather than a page?

    Links to PDFs, downloads and other non-HTML files resolve to something
    real and must not be reported as broken. Without this the uploads folder
    alone produced 58 false 'broken link' findings, which is exactly the kind
    of noise that gets a whole check ignored.
    """
    if not target or target == "/":
        return True
    candidates = {target, target.lstrip("/")}
    if assets:
        if target in assets or "/" + target.lstrip("/") in assets:
            return True
    if root:
        for candidate in candidates:
            if os.path.exists(os.path.join(root, candidate)):
                return True
        # extensionless path served as a directory index
        for suffix in ("index.html", ".html"):
            probe = os.path.join(root, target.lstrip("/").rstrip("/"))
            if os.path.exists(probe + suffix) or os.path.exists(
                    os.path.join(probe, suffix)):
                return True
        return False
    # Live mode: only a real non-200 proves a broken link.
    return not _remote_missing(target)


_REMOTE_CACHE = {}


def _remote_missing(target, origin=None, timeout=10):
    if not origin:
        return False
    if target in _REMOTE_CACHE:
        return _REMOTE_CACHE[target]
    try:
        from url_safety import safe_requests_head
        resp = safe_requests_head(origin + target, timeout=timeout,
                                  allow_redirects=True)
        missing = resp.status_code >= 400
    except Exception:
        missing = False
    _REMOTE_CACHE[target] = missing
    return missing


# ---------------------------------------------------------------------------
# Findings
# ---------------------------------------------------------------------------
EXEMPTIONS_FILE = ".seo-exemptions.json"


def load_exemptions(root):
    """
    Deliberate, recorded decisions not to act on a finding.

    Without this, anything correctly left alone -- an image WebP genuinely makes
    bigger, a noindex that is intentional -- is re-reported every single week.
    That is how a report earns the right to be ignored, and an ignored report is
    how the six defects survived three runs. An exemption needs a reason and a
    date, so it stays a decision on the record rather than a silent suppression.
    """
    if not root:
        return {}
    path = os.path.join(root, EXEMPTIONS_FILE)
    if not os.path.exists(path):
        return {}
    try:
        data = json.load(open(path, encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    out = {}
    for entry in data.get("exemptions", []):
        key = (entry.get("check"), entry.get("url"), entry.get("detail"))
        if entry.get("check") and entry.get("reason"):
            out[key] = entry
    return out


def _exempt_key(item):
    return (item["check"], item["url"], item.get("src") or item.get("target"))


def finding(check, url, evidence, **extra):
    meta = CHECKS[check]
    item = {
        "check": check,
        "title": meta["title"],
        "severity": meta["severity"],
        "category": meta["category"],
        "fix_class": meta.get("fix_class"),
        "autofixable": bool(meta.get("autofix")),
        "url": url,
        "evidence": evidence,
    }
    item.update(extra)
    return item


def audit(pages, assets, extras, base_url, root=None):
    findings = []
    ran = set()
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    origin = base_url.rstrip("/")

    parsed_pages = {}
    for path, data in pages.items():
        if data.get("html"):
            parsed_pages[path] = parse_page(data["html"])

    # ---- link graph -------------------------------------------------------
    inbound = {p: 0 for p in parsed_pages}
    asset_refs = {}
    for path, page in parsed_pages.items():
        outbound = set()
        for href, landmark in page.links:
            if landmark == "__asset__" or re.search(r"\.(js|css)(\?|$)", href or ""):
                asset_refs.setdefault(href, set()).add(path)
                continue
            target = resolve_internal(href, path, origin)
            if target and target != path:
                outbound.add(target)
        for target in outbound:
            if target in inbound:
                inbound[target] += 1
            elif target not in parsed_pages and not _target_exists(target, root, assets):
                findings.append(finding(
                    "link_graph.broken_internal_link", path,
                    "links to %s, which is not a page or file on this site" % target,
                    target=target))
        for image in page.images:
            if image.get("src"):
                asset_refs.setdefault(image["src"], set()).add(path)
        for srcset in page.picture_sources:
            asset_refs.setdefault(srcset.split()[0], set()).add(path)
    ran.update({"link_graph.broken_internal_link", "link_graph.orphan_page"})

    # ---- asset references -------------------------------------------------
    if root:
        for ref, used_on in sorted(asset_refs.items()):
            if not ref or ref.startswith(("http", "data:", "//")):
                continue
            local = os.path.join(root, ref.lstrip("/").split("?")[0])
            if not os.path.exists(local):
                findings.append(finding(
                    "link_graph.broken_asset_ref", sorted(used_on)[0],
                    "%s is referenced but does not exist" % ref,
                    target=ref, used_on=sorted(used_on)))
        ran.add("link_graph.broken_asset_ref")

    # ---- sitemap ----------------------------------------------------------
    smap = sitemap_urls(extras.get("sitemap.xml", ""))
    smap_paths = {_norm_path(urlparse(u).path) for u in smap}
    if smap:
        for path in sorted(smap_paths):
            page = parsed_pages.get(path)
            if page is None:
                findings.append(finding(
                    "sitemap.url_unreachable", path,
                    "listed in sitemap.xml but no page was found at that path"))
                continue
            robots = (page.meta.get("robots") or "").lower()
            if "noindex" in robots:
                findings.append(finding(
                    "sitemap.noindex_in_sitemap", path,
                    "sitemap submits this URL while the page sets robots=%r"
                    % page.meta.get("robots")))
        ran.update({"sitemap.url_unreachable", "sitemap.noindex_in_sitemap"})

        for path, page in sorted(parsed_pages.items()):
            robots = (page.meta.get("robots") or "").lower()
            if "noindex" in robots or path in smap_paths:
                continue
            if inbound.get(path, 0) > 0:
                findings.append(finding(
                    "sitemap.missing_from_sitemap", path,
                    "indexable and internally linked, but absent from sitemap.xml"))
        ran.add("sitemap.missing_from_sitemap")

        # Orphans are judged against the sitemap: those are the URLs the site
        # says it wants indexed.
        for path in sorted(smap_paths):
            if path == "/" or path not in parsed_pages:
                continue
            if inbound.get(path, 0) == 0:
                findings.append(finding(
                    "link_graph.orphan_page", path,
                    "no inbound internal link anywhere in the served HTML"))
    else:
        for path in sorted(parsed_pages):
            if path != "/" and inbound.get(path, 0) == 0:
                findings.append(finding(
                    "link_graph.orphan_page", path,
                    "no inbound internal link anywhere in the served HTML"))

    # ---- crawl coverage ---------------------------------------------------
    if smap_paths:
        unseen = sorted(smap_paths - set(parsed_pages))
        if extras.get("__truncated__") or unseen:
            findings.append(finding(
                "crawl.coverage_shortfall", origin,
                "read %d of %d sitemap URLs; %d never fetched%s"
                % (len(smap_paths & set(parsed_pages)), len(smap_paths), len(unseen),
                   " (crawl cap reached)" if extras.get("__truncated__") else ""),
                unseen=unseen[:50]))
    ran.add("crawl.coverage_shortfall")

    # ---- per page ---------------------------------------------------------
    for path, page in sorted(parsed_pages.items()):
        robots = (page.meta.get("robots") or "").lower()
        if "noindex" in robots:
            findings.append(finding(
                "indexability.noindex", path,
                "robots meta is %r" % page.meta.get("robots")))
            continue  # the checks below are about pages meant to rank

        title = re.sub(r"\s+", " ", (page.title or "")).strip()
        if title and len(title) < TITLE_MIN:
            findings.append(finding(
                "onpage.title_too_short", path,
                "%d characters: %r" % (len(title), title),
                current=title, length=len(title)))
        elif len(title) > TITLE_MAX:
            findings.append(finding(
                "onpage.title_too_long", path,
                "%d characters: %r" % (len(title), title),
                current=title, length=len(title)))

        desc = (page.meta.get("description") or "").strip()
        if desc and len(desc) < DESC_MIN:
            findings.append(finding(
                "onpage.meta_description_too_short", path,
                "%d characters" % len(desc), current=desc, length=len(desc)))
        elif len(desc) > DESC_MAX:
            findings.append(finding(
                "onpage.meta_description_too_long", path,
                "%d characters" % len(desc), current=desc, length=len(desc)))

        content_headings = [h for h in page.headings if not h[2]]
        chrome_headings = [h for h in page.headings if h[2]]
        h1s = [h for h in content_headings if h[0] == 1]
        if not h1s:
            findings.append(finding("onpage.h1_missing", path, "no H1 outside nav/header/footer"))
        elif len(h1s) > 1:
            findings.append(finding(
                "onpage.h1_multiple", path,
                "%d H1 elements: %s" % (len(h1s), [h[1] for h in h1s][:4])))

        if chrome_headings:
            findings.append(finding(
                "onpage.chrome_heading", path,
                "%d heading(s) inside nav/header/footer: %s"
                % (len(chrome_headings), [h[1] for h in chrome_headings][:8]),
                labels=[{"level": h[0], "text": h[1], "landmark": h[2]}
                        for h in chrome_headings]))

        levels = [h[0] for h in content_headings]
        for prev, nxt in zip(levels, levels[1:]):
            if nxt > prev + 1:
                findings.append(finding(
                    "onpage.heading_level_skip", path,
                    "outline jumps from h%d to h%d" % (prev, nxt)))
                break

        if not page.canonical:
            findings.append(finding("onpage.canonical_missing", path, "no rel=canonical"))

        # -- schema
        if not page.jsonld:
            findings.append(finding("schema.missing_on_page", path, "no JSON-LD blocks"))
        for index, block in enumerate(page.jsonld):
            try:
                json.loads(block)
            except ValueError as exc:
                findings.append(finding(
                    "schema.invalid_json", path,
                    "JSON-LD block %d does not parse: %s" % (index + 1, exc)))

        # -- AEO: question headings without FAQPage
        questions = [h[1] for h in content_headings if h[1].rstrip().endswith("?")]
        if len(questions) >= 2 and '"FAQPage"' not in " ".join(page.jsonld):
            findings.append(finding(
                "aeo.qa_page_without_faq_schema", path,
                "%d question headings but no FAQPage schema" % len(questions),
                questions=questions[:10]))

        # -- images
        for image in page.images:
            src = image.get("src") or ""
            if image.get("alt") is None:
                findings.append(finding(
                    "images.missing_alt", path, "no alt attribute on %s" % src,
                    src=src))
            if not image.get("width") or not image.get("height"):
                findings.append(finding(
                    "images.missing_dimensions", path,
                    "no width/height on %s" % src, src=src))
            ext = os.path.splitext(src.split("?")[0])[1].lower()
            if ext in RASTER_FORMATS and not image.get("in_picture"):
                findings.append(finding(
                    "images.legacy_format", path,
                    "%s is %s with no modern-format alternative" % (src, ext.lstrip(".")),
                    src=src))
            if root and src.startswith("/"):
                local = os.path.join(root, src.lstrip("/").split("?")[0])
                if os.path.exists(local):
                    size = os.path.getsize(local)
                    if size > IMAGE_WARN_BYTES:
                        findings.append(finding(
                            "images.oversized", path,
                            "%s is %d KB" % (src, size // 1024), src=src, bytes=size))

    ran.update({
        "onpage.title_too_short", "onpage.title_too_long",
        "onpage.meta_description_too_short", "onpage.meta_description_too_long",
        "onpage.h1_missing", "onpage.h1_multiple", "onpage.chrome_heading",
        "onpage.heading_level_skip", "onpage.canonical_missing",
        "schema.invalid_json", "schema.missing_on_page",
        "images.missing_alt", "images.missing_dimensions", "images.legacy_format",
        "indexability.noindex", "aeo.qa_page_without_faq_schema",
    })
    if root:
        ran.add("images.oversized")

    # ---- site-wide AEO / GEO ---------------------------------------------
    if "llms.txt" not in extras:
        findings.append(finding("aeo.llms_txt_missing", origin, "no /llms.txt"))
    ran.add("aeo.llms_txt_missing")

    robots_txt = extras.get("robots.txt", "")
    if robots_txt:
        blocked = []
        for agent in AI_AGENTS:
            pattern = re.compile(
                r"user-agent:\s*%s\s*(.*?)(?=\nuser-agent:|\Z)" % re.escape(agent),
                re.I | re.S)
            match = pattern.search(robots_txt)
            if match and re.search(r"^\s*disallow:\s*/\s*$", match.group(1), re.I | re.M):
                blocked.append(agent)
        if blocked:
            findings.append(finding(
                "aeo.ai_crawler_blocked", origin,
                "robots.txt disallows: %s" % ", ".join(blocked), agents=blocked))
        ran.add("aeo.ai_crawler_blocked")

    all_ld = " ".join(b for p in parsed_pages.values() for b in p.jsonld)
    if not re.search(r'"@type"\s*:\s*"(Organization|LocalBusiness|ProfessionalService)"', all_ld):
        findings.append(finding(
            "geo.entity_missing", origin,
            "no Organization, LocalBusiness or ProfessionalService node found"))
    elif '"sameAs"' not in all_ld:
        findings.append(finding(
            "geo.sameas_missing", origin, "entity has no sameAs profile links"))
    ran.update({"geo.entity_missing", "geo.sameas_missing"})

    # ---- coverage manifest ------------------------------------------------
    counts = {}
    for item in findings:
        counts[item["check"]] = counts.get(item["check"], 0) + 1

    records = []
    for check_id, meta in CHECKS.items():
        if check_id in ran:
            status, reason = "ran", None
        elif not meta["implemented_by"]:
            status, reason = "unimplemented", "no implementation in this repo"
        elif meta["implemented_by"] != "site_audit.py":
            status, reason = "skipped", "owned by %s, not run in this pass" % meta["implemented_by"]
        else:
            status, reason = "skipped", "preconditions not met (no sitemap, robots.txt or local root)"
        records.append({
            "check": check_id,
            "category": meta["category"],
            "status": status,
            "reason": reason,
            "pages_checked": len(parsed_pages) if status == "ran" else 0,
            "findings": counts.get(check_id, 0),
            "checked_at": now if status == "ran" else None,
            "implemented_by": meta["implemented_by"],
        })

    # Recorded exemptions are separated out, never silently dropped.
    exemptions = load_exemptions(root)
    exempted = []
    if exemptions:
        kept = []
        for item in findings:
            detail = item.get("src") or item.get("target")
            # url-agnostic exemptions (an asset exempt everywhere it appears)
            # are keyed on the detail alone, so record them once, not per page.
            match = (exemptions.get((item["check"], item["url"], detail))
                     or exemptions.get((item["check"], None, detail))
                     or exemptions.get((item["check"], item["url"], None)))
            if match:
                item["exempt_reason"] = match.get("reason")
                item["exempt_since"] = match.get("since")
                exempted.append(item)
            else:
                kept.append(item)
        findings = kept
        counts = {}
        for item in findings:
            counts[item["check"]] = counts.get(item["check"], 0) + 1
        for record in records:
            record["findings"] = counts.get(record["check"], 0)

    order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
    findings.sort(key=lambda f: (order.get(f["severity"], 9), f["check"], f["url"]))

    return {
        "generated_at": now,
        "base_url": origin,
        "stats": {
            "pages_parsed": len(parsed_pages),
            "sitemap_urls": len(smap_paths),
            "sitemap_urls_unseen": len(smap_paths - set(parsed_pages)) if smap_paths else 0,
            "orphans": counts.get("link_graph.orphan_page", 0),
            "findings": len(findings),
            "by_severity": {
                sev: sum(1 for f in findings if f["severity"] == sev)
                for sev in ("critical", "high", "medium", "low", "info")
            },
            "autofixable": sum(1 for f in findings if f["autofixable"]),
            "needs_approval": sum(1 for f in findings if f["fix_class"] == "content"),
            "exempted": len(exempted),
        },
        "findings": findings,
        "exempted": exempted,
        "coverage": {"generated_at": now, "checks": records},
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def compare(previous, current):
    """
    Mechanical week-over-week diff.

    The mvp1.com.au weekly reports compared last week's prose to this week's
    prose, so five of eight categories were byte-identical carried-forward text
    that read as a stable result. Findings carry stable (check, url) keys, so
    the diff is computed, not narrated -- and a finding that disappears because
    nobody checked shows up as a coverage regression, not as a win.
    """
    def key(item):
        return (item["check"], item["url"], item.get("src") or item.get("target") or "")

    before = {key(f): f for f in previous.get("findings", [])}
    after = {key(f): f for f in current.get("findings", [])}

    cleared = [before[k] for k in sorted(before.keys() - after.keys())]
    appeared = [after[k] for k in sorted(after.keys() - before.keys())]

    prev_cov = {c["check"]: c for c in previous.get("coverage", {}).get("checks", [])}
    curr_cov = {c["check"]: c for c in current.get("coverage", {}).get("checks", [])}
    regressions = [
        cid for cid, rec in curr_cov.items()
        if rec.get("status") != "ran" and prev_cov.get(cid, {}).get("status") == "ran"
    ]

    # A finding cannot be called "cleared" by a check that stopped running.
    unverified = [f for f in cleared if curr_cov.get(f["check"], {}).get("status") != "ran"]
    verified = [f for f in cleared if f not in unverified]

    return {
        "cleared": verified,
        "cleared_unverified": unverified,
        "appeared": appeared,
        "coverage_regressions": regressions,
        "summary": {
            "cleared": len(verified),
            "cleared_unverified": len(unverified),
            "appeared": len(appeared),
            "still_open": len(after) - len(appeared),
            "coverage_regressions": len(regressions),
        },
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--root", help="path to a static site on disk")
    source.add_argument("--url", help="base URL of a live site to crawl")
    parser.add_argument("--base-url", help="canonical origin (required with --root)")
    parser.add_argument("--max-pages", type=int, default=500)
    parser.add_argument("--timeout", type=int, default=20)
    parser.add_argument("--json", action="store_true", help="full JSON to stdout")
    parser.add_argument("--output", help="write the JSON result here")
    parser.add_argument("--fail-on", choices=["critical", "high", "medium", "low"],
                        help="exit 1 if any finding is at or above this severity")
    parser.add_argument("--compare", metavar="PREVIOUS_JSON",
                        help="diff this run against a previous site_audit result")
    args = parser.parse_args()

    if args.root:
        base = (args.base_url or "https://example.com").rstrip("/")
        pages, assets, extras = load_from_root(args.root, base)
        root = args.root
    else:
        base = args.url.rstrip("/")
        pages, assets, extras = load_from_url(base, args.max_pages, args.timeout)
        root = None

    if not pages:
        print("no pages found", file=sys.stderr)
        return 2

    result = audit(pages, assets, extras, base, root=root)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            json.dump(result, handle, indent=2)

    if args.compare:
        try:
            previous = json.load(open(args.compare, encoding="utf-8"))
        except (OSError, ValueError) as exc:
            print("cannot read %s: %s" % (args.compare, exc), file=sys.stderr)
            return 2
        result["changed_since"] = compare(previous, result)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        stats = result["stats"]
        print("%s -- %d pages, %d sitemap URLs (%d unseen)"
              % (result["base_url"], stats["pages_parsed"],
                 stats["sitemap_urls"], stats["sitemap_urls_unseen"]))
        sev = stats["by_severity"]
        print("%d findings: %d critical, %d high, %d medium, %d low, %d info"
              % (stats["findings"], sev["critical"], sev["high"],
                 sev["medium"], sev["low"], sev["info"]))
        print("%d autofixable, %d need approval (reader-facing)\n"
              % (stats["autofixable"], stats["needs_approval"]))
        grouped = {}
        for item in result["findings"]:
            grouped.setdefault(item["check"], []).append(item)
        for check, items in grouped.items():
            head = items[0]
            print("%-9s %-38s %d  %s" % (
                head["severity"].upper(), check, len(items),
                "[autofix]" if head["autofixable"]
                else "[approval]" if head["fix_class"] == "content" else ""))
            for item in items[:3]:
                print("            %s -- %s" % (item["url"], item["evidence"][:96]))
            if len(items) > 3:
                print("            ... and %d more" % (len(items) - 3))
        diff = result.get("changed_since")
        if diff:
            summary = diff["summary"]
            print("\nsince the previous run: %d cleared, %d new, %d still open"
                  % (summary["cleared"], summary["appeared"], summary["still_open"]))
            if summary["coverage_regressions"]:
                print("  WARNING: %d check(s) ran last time and did not run now: %s"
                      % (summary["coverage_regressions"],
                         ", ".join(diff["coverage_regressions"])))
            if summary["cleared_unverified"]:
                print("  %d finding(s) vanished only because their check stopped "
                      "running -- not fixed" % summary["cleared_unverified"])
        if args.output:
            print("\nwritten to %s" % args.output)

    if args.fail_on:
        order = ["critical", "high", "medium", "low"]
        limit = order.index(args.fail_on)
        if any(order.index(f["severity"]) <= limit
               for f in result["findings"] if f["severity"] in order):
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
