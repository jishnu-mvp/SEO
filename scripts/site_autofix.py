#!/usr/bin/env python3
"""
Apply the mechanical fixes for site_audit.py findings, and queue the rest.

The split this script enforces is the whole point of it:

  technical  -- not rendered as reader-facing copy (sitemap entries, asset
                references, image formats and dimensions, markup tags). Applied
                automatically and shipped without waiting for anyone.
  content    -- changes what a visitor actually reads or sees (copy, headings,
                alt text, FAQ answers). Never touched. Written to an approval
                queue with the evidence needed to decide.
  proposal   -- technical by classification but needs language a script cannot
                write well (titles, meta descriptions). Emitted as a drafting
                brief with the constraints attached, for the agent to author.

That mirrors the standing rule in mvp1-website/CLAUDE.md, so an unattended
weekly run can ship everything safe and stop cleanly at everything that is not.

Every fix is idempotent: running twice changes nothing the second time.
Nothing is deleted. CSS changes are additive, so a selector that used to apply
still applies.

Usage:
    python site_autofix.py --audit audit.json --root ../mvp1-website
    python site_autofix.py --audit audit.json --root . --dry-run
    python site_autofix.py --audit audit.json --root . --only sitemap.noindex_in_sitemap
    python site_autofix.py --audit audit.json --root . --queue approvals.json

Output: JSON summary of what was applied, skipped and queued.
Exit 0 always unless --strict and a requested fix failed.
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPTS_DIR)

from audit_coverage import CHECKS  # noqa: E402
from site_audit import image_dimensions  # noqa: E402

CHROME_CLASS = "navgroup-h"
PICTURE_SHIM = "picture{display:contents}"


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def _read(path):
    return open(path, encoding="utf-8", errors="replace").read()


def _write(path, text, dry_run):
    if dry_run:
        return
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(text)


def record_exemption(root, check, detail, reason, dry_run):
    """
    Write a dated, reasoned decision not to act on a finding.

    Anything correctly left alone would otherwise be re-reported every week
    until the report itself is ignored. An exemption carries a reason and a
    date so it stays reviewable, not a silent suppression.
    """
    path = os.path.join(root, ".seo-exemptions.json")
    data = {"exemptions": []}
    if os.path.exists(path):
        try:
            data = json.load(open(path, encoding="utf-8"))
        except (OSError, ValueError):
            pass
    data.setdefault("exemptions", [])
    for entry in data["exemptions"]:
        if entry.get("check") == check and entry.get("detail") == detail:
            return
    data["exemptions"].append({
        "check": check,
        "url": None,
        "detail": detail,
        "reason": reason,
        "since": datetime.now(timezone.utc).date().isoformat(),
        "recorded_by": "site_autofix.py",
    })
    if not dry_run:
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2)


def _html_files(root):
    skip = {".git", "node_modules", ".audit-history", "scripts"}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in skip and not d.startswith(".")]
        for name in filenames:
            if name.endswith(".html"):
                yield os.path.join(dirpath, name)


def _css_files(root):
    skip = {".git", "node_modules", ".audit-history"}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in skip and not d.startswith(".")]
        for name in filenames:
            if name.endswith(".css"):
                yield os.path.join(dirpath, name)


# ---------------------------------------------------------------------------
# fix: sitemap entries
# ---------------------------------------------------------------------------
def fix_sitemap(findings, root, dry_run):
    """Drop noindexed and unreachable URLs; add indexable pages that are absent."""
    path = os.path.join(root, "sitemap.xml")
    if not os.path.exists(path):
        return [], ["no sitemap.xml at the site root"]

    xml = _read(path)
    original = xml
    applied, notes = [], []

    drop = [f for f in findings
            if f["check"] in ("sitemap.noindex_in_sitemap", "sitemap.url_unreachable")]
    for item in drop:
        target = item["url"].rstrip("/")
        pattern = re.compile(
            r"\s*<url>\s*<loc>[^<]*%s/?</loc>.*?</url>" % re.escape(target), re.S)
        xml, count = pattern.subn("", xml)
        if count:
            applied.append({"check": item["check"], "url": item["url"],
                            "action": "removed from sitemap.xml"})

    add = [f for f in findings if f["check"] == "sitemap.missing_from_sitemap"]
    if add:
        base = ""
        first = re.search(r"<loc>(https?://[^/]+)", xml)
        if first:
            base = first.group(1)
        today = datetime.now(timezone.utc).date().isoformat()
        block = ""
        for item in add:
            loc = base + item["url"]
            if "<loc>%s</loc>" % loc in xml:
                continue
            block += ("  <url>\n    <loc>%s</loc>\n    <lastmod>%s</lastmod>\n"
                      "    <priority>0.6</priority>\n  </url>\n" % (loc, today))
            applied.append({"check": item["check"], "url": item["url"],
                            "action": "added to sitemap.xml"})
        if block:
            xml = xml.replace("</urlset>", block + "</urlset>")

    if xml != original:
        _write(path, xml, dry_run)
    return applied, notes


# ---------------------------------------------------------------------------
# fix: broken asset references
# ---------------------------------------------------------------------------
def fix_broken_assets(findings, root, dry_run):
    """
    Repoint a reference whose file exists under a different extension.

    This is the guardbay.jpg / guardbay.png case: the markup asked for one
    extension, the repo held another, and the homepage served a 404 logo for
    weeks. Only acted on when exactly one candidate exists, so it can never
    guess between two plausible files.
    """
    applied, notes = [], []
    items = [f for f in findings if f["check"] == "link_graph.broken_asset_ref"]
    if not items:
        return applied, notes

    rewrites = {}
    for item in items:
        ref = item.get("target") or ""
        stem, _ = os.path.splitext(ref)
        directory = os.path.join(root, os.path.dirname(ref.lstrip("/")))
        base = os.path.basename(stem)
        if not os.path.isdir(directory):
            notes.append("no directory for %s" % ref)
            continue
        candidates = [n for n in os.listdir(directory)
                      if os.path.splitext(n)[0] == base]
        if len(candidates) == 1:
            rewrites[ref] = os.path.dirname(ref) + "/" + candidates[0]
        else:
            notes.append("%s: %d candidate files, not guessing" % (ref, len(candidates)))

    if not rewrites:
        return applied, notes

    for html_path in _html_files(root):
        text = _read(html_path)
        original = text
        for old, new in rewrites.items():
            text = text.replace(old, new)
        if text != original:
            _write(html_path, text, dry_run)
    for old, new in rewrites.items():
        applied.append({"check": "link_graph.broken_asset_ref", "url": old,
                        "action": "repointed to %s" % new})
    return applied, notes


# ---------------------------------------------------------------------------
# fix: navigation chrome marked up as headings
# ---------------------------------------------------------------------------
def fix_chrome_headings(findings, root, dry_run):
    """
    Turn nav/header/footer labels into paragraphs, keeping their styling.

    Same words, same position, same rendering -- only the tag changes, so the
    page a visitor sees is untouched. CSS is handled additively: any rule whose
    selector targets a bare hN gains a parallel selector for the new class, so
    nothing that used to be styled stops being styled.
    """
    applied, notes = [], []
    labels = set()
    for item in findings:
        if item["check"] != "onpage.chrome_heading":
            continue
        for entry in item.get("labels", []):
            labels.add((entry["level"], entry["text"]))
    if not labels:
        return applied, notes

    landmark_re = re.compile(r"<(nav|header|footer)\b[^>]*>.*?</\1>", re.S | re.I)
    heading_re = re.compile(r"<h([1-6])(\s[^>]*)?>(.*?)</h\1>", re.S | re.I)
    touched = 0

    for html_path in _html_files(root):
        text = _read(html_path)
        original = text

        def convert_region(match):
            region = match.group(0)

            def to_paragraph(hit):
                attrs = hit.group(2) or ""
                inner = hit.group(3)
                plain = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", inner)).strip()
                if not plain:
                    return hit.group(0)
                if 'class="' in attrs:
                    attrs = re.sub(r'class="([^"]*)"',
                                   lambda m: 'class="%s %s"' % (m.group(1), CHROME_CLASS),
                                   attrs)
                else:
                    attrs = ' class="%s"%s' % (CHROME_CLASS, attrs)
                return "<p%s>%s</p>" % (attrs, inner)

            return heading_re.sub(to_paragraph, region)

        text = landmark_re.sub(convert_region, text)
        if text != original:
            _write(html_path, text, dry_run)
            touched += 1

    if not touched:
        return applied, notes

    for css_path in _css_files(root):
        css = _read(css_path)
        original = css

        def widen(match):
            selector = match.group(1)
            if CHROME_CLASS in selector:
                return match.group(0)
            parts = [p.strip() for p in selector.split(",")]
            extra = []
            for part in parts:
                widened = re.sub(r"(^|\s)h[1-6](\s|$|:)",
                                 lambda m: "%s.%s%s" % (m.group(1), CHROME_CLASS, m.group(2)),
                                 part)
                if widened != part:
                    extra.append(widened)
            if not extra:
                return match.group(0)
            return "%s,%s{" % (selector, ",".join(extra))

        css = re.sub(r"([^{}]+)\{", widen, css)
        if PICTURE_SHIM not in css and "img{" in css:
            css = css.replace("img{", PICTURE_SHIM + "\nimg{", 1)
        if css != original:
            _write(css_path, css, dry_run)

    applied.append({
        "check": "onpage.chrome_heading",
        "url": "site-wide",
        "action": "converted %d heading(s) in %d file(s) to <p class=\"%s\">; "
                  "CSS selectors widened additively"
                  % (len(labels), touched, CHROME_CLASS),
    })
    return applied, notes


# ---------------------------------------------------------------------------
# fix: image dimensions
# ---------------------------------------------------------------------------
def fix_image_dimensions(findings, root, dry_run):
    """Add width/height read from each file's own header, to stop layout shift."""
    applied, notes = [], []
    wanted = {}
    for item in findings:
        if item["check"] != "images.missing_dimensions":
            continue
        src = item.get("src") or ""
        if src.startswith("/"):
            wanted.setdefault(src, set()).add(item["url"])
    if not wanted:
        return applied, notes

    sizes = {}
    for src in wanted:
        local = os.path.join(root, src.lstrip("/").split("?")[0])
        size = image_dimensions(local) if os.path.exists(local) else None
        if size:
            sizes[src] = size
        else:
            notes.append("could not read intrinsic size for %s" % src)
    if not sizes:
        return applied, notes

    count = 0
    for html_path in _html_files(root):
        text = _read(html_path)
        original = text

        def add_dims(match):
            tag = match.group(0)
            src_match = re.search(r'src="([^"]+)"', tag)
            if not src_match or src_match.group(1) not in sizes:
                return tag
            if re.search(r'\bwidth=', tag) and re.search(r'\bheight=', tag):
                return tag
            width, height = sizes[src_match.group(1)]
            return tag[:-1].rstrip() + ' width="%d" height="%d">' % (width, height)

        text = re.sub(r"<img\b[^>]*>", add_dims, text)
        if text != original:
            _write(html_path, text, dry_run)
            count += 1

    applied.append({"check": "images.missing_dimensions", "url": "site-wide",
                    "action": "added width/height for %d image(s) across %d file(s)"
                              % (len(sizes), count)})
    return applied, notes


# ---------------------------------------------------------------------------
# fix: legacy image formats
# ---------------------------------------------------------------------------
def fix_image_formats(findings, root, dry_run, quality=82):
    """
    Convert rasters to WebP and serve them through <picture>.

    Keeps the original as the <img> fallback, so a failed conversion or an old
    browser still renders. Skips any image WebP does not actually shrink --
    shipping a larger file to look modern is not an optimisation.
    """
    applied, notes = [], []
    if not shutil.which("cwebp"):
        return applied, ["cwebp not installed; skipped image conversion "
                         "(apt-get install webp, or brew install webp)"]

    sources = set()
    for item in findings:
        if item["check"] != "images.legacy_format":
            continue
        src = item.get("src") or ""
        if src.startswith("/"):
            sources.add(src.split("?")[0])

    converted, saved = {}, 0
    for src in sorted(sources):
        local = os.path.join(root, src.lstrip("/"))
        if not os.path.exists(local):
            continue
        target = os.path.splitext(local)[0] + ".webp"
        web_src = os.path.splitext(src)[0] + ".webp"
        if os.path.exists(target):
            converted[src] = web_src
            continue
        if dry_run:
            converted[src] = web_src
            continue
        lossless = local.lower().endswith(".png")
        cmd = ["cwebp", "-quiet"] + (["-z", "9", "-lossless"] if lossless
                                     else ["-q", str(quality)]) + [local, "-o", target]
        try:
            subprocess.run(cmd, check=True, capture_output=True, timeout=120)
        except (subprocess.SubprocessError, OSError) as exc:
            notes.append("cwebp failed for %s: %s" % (src, exc))
            continue
        before, after = os.path.getsize(local), os.path.getsize(target)
        if lossless and after >= before:  # retry with high-quality lossy + alpha
            try:
                subprocess.run(["cwebp", "-quiet", "-q", "88", "-alpha_q", "100",
                                local, "-o", target], check=True,
                               capture_output=True, timeout=120)
                after = os.path.getsize(target)
            except (subprocess.SubprocessError, OSError):
                pass
        if after >= before * 0.9:
            os.remove(target)
            notes.append("%s: webp was not meaningfully smaller, left as-is" % src)
            record_exemption(
                root, "images.legacy_format", src,
                "WebP encodes larger than the original (%d vs %d bytes); shipping "
                "a bigger file to look modern is not an optimisation"
                % (after, before), dry_run)
            continue
        converted[src] = web_src
        saved += before - after

    if not converted:
        return applied, notes

    files_touched = 0
    for html_path in _html_files(root):
        text = _read(html_path)
        original = text

        def wrap(match):
            tag = match.group(0)
            start = match.start()
            src_match = re.search(r'src="([^"]+)"', tag)
            if not src_match:
                return tag
            src = src_match.group(1).split("?")[0]
            if src not in converted:
                return tag
            before = text[:start]
            if before.rfind("<picture") > before.rfind("</picture>"):
                return tag
            return ('<picture><source srcset="%s" type="image/webp">%s</picture>'
                    % (converted[src], tag))

        text = re.sub(r"<img\b[^>]*>", wrap, text)
        if text != original:
            _write(html_path, text, dry_run)
            files_touched += 1

    for css_path in _css_files(root):
        css = _read(css_path)
        if PICTURE_SHIM not in css and re.search(r"(^|\})img\{", css):
            css = re.sub(r"(^|\})img\{", lambda m: m.group(1) + PICTURE_SHIM + "\nimg{",
                         css, count=1)
            _write(css_path, css, dry_run)

    applied.append({
        "check": "images.legacy_format", "url": "site-wide",
        "action": "converted %d image(s) to WebP and wrapped them in <picture> "
                  "across %d file(s); %d KB saved"
                  % (len(converted), files_touched, saved // 1024),
    })
    return applied, notes


# ---------------------------------------------------------------------------
# queue + proposals
# ---------------------------------------------------------------------------
PROPOSAL_CONSTRAINTS = {
    "onpage.title_too_short": "Rewrite to 30-60 characters. Describe the page "
                              "from its own H1 and lede. Keep the brand suffix.",
    "onpage.title_too_long": "Trim to 60 characters or fewer without losing the "
                             "distinguishing term. Keep the brand suffix.",
    "onpage.meta_description_too_short": "Rewrite to 70-155 characters, "
                                         "describing what the page delivers.",
    "onpage.meta_description_too_long": "Trim to 155 characters or fewer, "
                                        "keeping the specifics, dropping filler.",
}


def build_queue(findings):
    """Split what a human must decide from what the agent must write."""
    approvals, proposals = [], []
    for item in findings:
        check = item["check"]
        meta = CHECKS.get(check, {})
        if meta.get("autofix"):
            continue
        entry = {
            "check": check,
            "title": item["title"],
            "severity": item["severity"],
            "url": item["url"],
            "evidence": item["evidence"],
        }
        if check in PROPOSAL_CONSTRAINTS:
            entry["current"] = item.get("current")
            entry["constraint"] = PROPOSAL_CONSTRAINTS[check]
            proposals.append(entry)
        elif meta.get("fix_class") == "content":
            entry["why_approval"] = ("changes what a visitor reads or sees, so it "
                                     "waits for an explicit decision")
            approvals.append(entry)
    return approvals, proposals


FIXERS = [
    ("sitemap", fix_sitemap),
    ("broken_assets", fix_broken_assets),
    ("chrome_headings", fix_chrome_headings),
    ("image_dimensions", fix_image_dimensions),
    ("image_formats", fix_image_formats),
]


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--audit", required=True, help="site_audit.py JSON output")
    parser.add_argument("--root", required=True, help="site root on disk")
    parser.add_argument("--dry-run", action="store_true", help="report, change nothing")
    parser.add_argument("--only", action="append", default=[],
                        help="restrict to these check ids (repeatable)")
    parser.add_argument("--queue", help="write the approval/proposal queue here")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--max-passes", type=int, default=4,
                        help="re-audit and re-fix until stable (default 4)")
    parser.add_argument("--strict", action="store_true",
                        help="exit 1 if any requested fix could not be applied")
    args = parser.parse_args()

    data = json.load(open(args.audit, encoding="utf-8"))
    findings = data.get("findings", [])
    if args.only:
        findings = [f for f in findings if f["check"] in args.only]

    applied, notes = [], []
    passes = 0
    while True:
        passes += 1
        before = len(applied)
        for _, fixer in FIXERS:
            got, said = fixer(findings, args.root, args.dry_run)
            applied.extend(got)
            notes.extend(said)
        if passes >= args.max_passes or args.dry_run or len(applied) == before:
            break
        # One fix can expose the next: repointing a broken reference reveals an
        # image that now needs converting. Re-audit and keep going until the
        # site stops changing, so a weekly run does not leave work for next week.
        from site_audit import audit, load_from_root
        pages, assets, extras = load_from_root(args.root, data.get("base_url", ""))
        findings = audit(pages, assets, extras, data.get("base_url", ""),
                         root=args.root)["findings"]
        if args.only:
            findings = [f for f in findings if f["check"] in args.only]

    approvals, proposals = build_queue(findings)

    result = {
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "root": args.root,
        "dry_run": args.dry_run,
        "applied": applied,
        "notes": notes,
        "needs_approval": approvals,
        "needs_drafting": proposals,
        "passes": passes,
        "summary": {
            "fixes_applied": len(applied),
            "awaiting_approval": len(approvals),
            "awaiting_drafting": len(proposals),
        },
    }

    if args.queue:
        with open(args.queue, "w", encoding="utf-8") as handle:
            json.dump({"needs_approval": approvals, "needs_drafting": proposals},
                      handle, indent=2)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        head = "DRY RUN -- nothing written" if args.dry_run else "applied"
        print("%s: %d fix(es)" % (head, len(applied)))
        for item in applied:
            print("  %-34s %s" % (item["check"], item["action"]))
        for note in notes:
            print("  note: %s" % note)
        print("\n%d item(s) need your approval (reader-facing):" % len(approvals))
        for item in approvals[:10]:
            print("  %-34s %s" % (item["check"], item["url"]))
        print("%d item(s) need drafting by the agent:" % len(proposals))
        for item in proposals[:10]:
            print("  %-34s %s" % (item["check"], item["url"]))
        if args.queue:
            print("\nqueue written to %s" % args.queue)

    if args.strict and notes:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
