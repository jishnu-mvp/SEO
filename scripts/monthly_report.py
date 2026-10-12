#!/usr/bin/env python3
"""
Monthly SEO / AEO / GEO report generator (PDF).

Builds a narrative leadership report from one JSON file, on top of the
canonical report helpers in google_report.py (same A4 stylesheet, title
page, table of contents, chart wrapper, WeasyPrint writer and the same
post-generation PDF review gate).  google_report.py stays the single
source of truth for look and feel; this module only adds the monthly
layout, so the weekly and monthly reports cannot drift apart.

Input JSON (see mvp1-website/.audit-history/mvp1.com.au/monthly-YYYY-MM.json):

    {
      "title": "Monthly SEO, AEO and GEO Report",
      "period": "September 2026",
      "prepared": "12 October 2026",
      "score": 93, "score_label": "SEO Health Score",
      "summary": "paragraph",
      "cards": [{"value": "93/100", "label": "Health score", "color": "#2d6a4f"}],
      "charts": {"position": {"type": "bars", ...}, ...},
      "sections": [{"heading": "...", "intro": "...", "chart": "position",
                    "bullets": ["..."], "table": {"head": [...], "rows": [[...]]},
                    "callout": "..."}],
      "next_steps": [{"name": "...", "timeframe": "...", "items": ["..."]}],
      "methodology": ["..."]
    }

Chart specs:
    {"type": "bars",   "labels": [...], "values": [...], "highlight_from": 2,
                       "invert": false, "ylabel": "...", "fmt": "{:.1f}", "caption": "..."}
    {"type": "paired", "panels": [{"title": "...", "before": 1, "after": 2}],
                       "before_label": "...", "after_label": "...", "caption": "..."}
    {"type": "grouped","labels": [...], "before": [...], "after": [...],
                       "before_label": "...", "after_label": "...", "caption": "..."}
    {"type": "line",   "x": [...], "y": [...], "refs": [{"value": 8.0, "label": "...", "pos": "below"}],
                       "ylabel": "...", "caption": "..."}

Usage:
    python monthly_report.py --data monthly-2026-09.json --domain mvp1.com.au \\
        --output-dir ./out --json

Exit status is 1 when the PDF could not be written or the review gate
reports anything other than PASS.
"""

import argparse
import json
import sys
from html import escape
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import google_report as gr  # noqa: E402

BLUE = "#2f6fb0"      # after / current (passes the dataviz palette validator)
GOLD = "#b8860b"      # reference lines and accents
GREY = "#94a3b8"      # before / baseline


def _style_axes(ax):
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.grid(axis="y", color="#e5e7eb", linewidth=0.8)
    ax.set_axisbelow(True)


def _save(fig, out_dir: Path, name: str) -> str:
    path = out_dir / f"{name}.png"
    fig.savefig(path, dpi=200, bbox_inches="tight", facecolor="white")
    return str(path)


def chart_bars(spec: dict, out_dir: Path, name: str) -> str:
    import matplotlib.pyplot as plt
    labels, values = spec["labels"], spec["values"]
    start = spec.get("highlight_from", 0)
    colors = [GREY if i < start else BLUE for i in range(len(values))]
    fig, ax = plt.subplots(figsize=(7.2, 2.7))
    bars = ax.bar(range(len(values)), values, color=colors, width=0.62)
    fmt = spec.get("fmt", "{:g}")
    for b, v in zip(bars, values):
        ax.text(b.get_x() + b.get_width() / 2, b.get_height(), fmt.format(v),
                ha="center", va="bottom", fontsize=9, fontweight="bold")
    ax.set_xticks(range(len(values)))
    ax.set_xticklabels(labels, fontsize=8)
    ax.set_ylabel(spec.get("ylabel", ""), fontsize=9)
    if spec.get("invert"):
        ax.set_ylim(max(values) * 1.18, 0)
    else:
        ax.set_ylim(0, max(values) * 1.18)
    _style_axes(ax)
    return _save(fig, out_dir, name)


def chart_paired(spec: dict, out_dir: Path, name: str) -> str:
    import matplotlib.pyplot as plt
    panels = spec["panels"]
    fig, axes = plt.subplots(1, len(panels), figsize=(7.2, 2.4))
    if len(panels) == 1:
        axes = [axes]
    for ax, p in zip(axes, panels):
        vals = [p["before"], p["after"]]
        bars = ax.bar([0, 1], vals, color=[GREY, BLUE], width=0.6)
        for b, v in zip(bars, vals):
            ax.text(b.get_x() + b.get_width() / 2, b.get_height(), f"{v:g}",
                    ha="center", va="bottom", fontsize=9, fontweight="bold")
        ax.set_title(p["title"], fontsize=9.5, fontweight="bold")
        ax.set_xticks([0, 1])
        ax.set_xticklabels([spec.get("before_label", "Before"),
                            spec.get("after_label", "After")], fontsize=8)
        ax.set_ylim(0, max(vals) * 1.25)
        _style_axes(ax)
    fig.tight_layout()
    return _save(fig, out_dir, name)


def chart_grouped(spec: dict, out_dir: Path, name: str) -> str:
    import matplotlib.pyplot as plt
    labels = spec["labels"]
    n = len(labels)
    fig, ax = plt.subplots(figsize=(7.2, 1.95))
    w = 0.38
    xs = list(range(n))
    b1 = ax.bar([x - w / 2 for x in xs], spec["before"], w, color=GREY,
                label=spec.get("before_label", "Before"))
    b2 = ax.bar([x + w / 2 for x in xs], spec["after"], w, color=BLUE,
                label=spec.get("after_label", "After"))
    for bars in (b1, b2):
        for b in bars:
            ax.text(b.get_x() + b.get_width() / 2, b.get_height(), f"{b.get_height():g}",
                    ha="center", va="bottom", fontsize=8.5)
    ax.set_xticks(xs)
    ax.set_xticklabels(labels, fontsize=8)
    ax.set_ylim(0, 122)
    ax.set_yticks([0, 20, 40, 60, 80, 100])
    ax.legend(frameon=False, fontsize=8, loc="upper left", ncol=2)
    _style_axes(ax)
    return _save(fig, out_dir, name)


def chart_line(spec: dict, out_dir: Path, name: str) -> str:
    import matplotlib.pyplot as plt
    x, y = spec["x"], spec["y"]
    fig, ax = plt.subplots(figsize=(7.2, 2.8))
    ax.plot(range(len(y)), y, color=BLUE, linewidth=1.8, marker="o", markersize=3.2)
    for ref in spec.get("refs", []):
        ax.axhline(ref["value"], color=GOLD, linewidth=1.3, linestyle="--")
        below = ref.get("pos") == "below"
        ax.text(len(y) - 0.4, ref["value"], " " + ref["label"], color=GOLD, fontsize=8,
                va="top" if below else "bottom", ha="left", fontweight="bold",
                clip_on=False)
    step = max(1, len(x) // 10)
    ax.set_xticks(range(0, len(x), step))
    ax.set_xticklabels([x[i] for i in range(0, len(x), step)], fontsize=8)
    ax.set_xlabel(spec.get("xlabel", ""), fontsize=9)
    ax.set_ylabel(spec.get("ylabel", ""), fontsize=9)
    ax.set_ylim(0, max(y) * 1.18)
    _style_axes(ax)
    fig.subplots_adjust(right=0.72)
    return _save(fig, out_dir, name)


CHART_BUILDERS = {"bars": chart_bars, "paired": chart_paired,
                  "grouped": chart_grouped, "line": chart_line}


def _table_html(table: dict) -> str:
    head = "".join(f"<th>{escape(str(h))}</th>" for h in table["head"])
    rows = []
    for row in table["rows"]:
        rows.append("<tr>" + "".join(f"<td>{escape(str(c))}</td>" for c in row) + "</tr>")
    return f"  <table>\n    <thead><tr>{head}</tr></thead>\n    <tbody>\n      " + \
           "\n      ".join(rows) + "\n    </tbody>\n  </table>\n"


def _title_page(data: dict, domain: str) -> str:
    score_html = ""
    if data.get("score") is not None:
        score_html = (
            '  <div class="score-box">\n'
            f'    <div class="score-number">{data["score"]}'
            '<span style="font-size: 20pt; color: #94a3b8;">/100</span></div>\n'
            f'    <div class="score-label">{escape(data.get("score_label", ""))}</div>\n'
            '  </div>\n'
        )
    return (
        '\n<div class="title-page">\n'
        f'  <div class="badge">{escape(data["title"])}</div>\n'
        f'  <h1>{escape(domain)}</h1>\n'
        f'  <div class="subtitle">{escape(data["period"])}</div>\n'
        f'{score_html}'
        '  <div class="meta">\n'
        f'    <span>Prepared {escape(data.get("prepared", ""))}</span>\n'
        '    <span>SEO, AEO and GEO</span>\n'
        '  </div>\n'
        '</div>\n'
    )


def _section(num: int, sec: dict, chart_paths: dict, fig_counter: list) -> str:
    lines = ['\n<div class="section">',
             '  <div class="section-header">',
             f'    <h2>{num}. {escape(sec["heading"])}</h2>',
             '  </div>', '']
    if sec.get("intro"):
        lines.append(f'  <p>{escape(sec["intro"])}</p>')
    if sec.get("table"):
        lines.append(_table_html(sec["table"]))
    for key in sec.get("charts", [sec["chart"]] if sec.get("chart") else []):
        path = chart_paths.get(key)
        if path:
            fig_counter[0] += 1
            lines.append(gr._chart_html(path, escape(chart_paths[key + ":caption"]),
                                        fig_counter[0], alt=key))
    if sec.get("bullets"):
        lines.append("  <ul>")
        lines.extend(f"    <li>{escape(b)}</li>" for b in sec["bullets"])
        lines.append("  </ul>")
    if sec.get("callout"):
        lines.append(f'  <div class="success-box"><p>{escape(sec["callout"])}</p></div>')
    lines.append("</div>")
    return "\n".join(lines)


def _cards(cards: list) -> str:
    if not cards:
        return ""
    rows = []
    for i in range(0, len(cards), 4):
        chunk = cards[i:i + 4]
        cols = "".join(
            f'    <div class="col">\n{gr._metric_card(escape(c["value"]), escape(c["label"]), c.get("color"))}    </div>\n'
            for c in chunk)
        rows.append(f'  <div class="four-col">\n{cols}  </div>\n')
    return "".join(rows)


def _next_steps(num: int, steps: list) -> str:
    lines = ['\n<div class="section">', '  <div class="section-header">',
             f'    <h2>{num}. Next Steps</h2>', '  </div>', '']
    for ph in steps:
        lines.append('  <div class="roadmap-phase">')
        lines.append(f'    <h4>{escape(ph["name"])} <span class="effort">{escape(ph.get("timeframe", ""))}</span></h4>')
        lines.append("    <ul>")
        lines.extend(f"      <li>{escape(i)}</li>" for i in ph["items"])
        lines.append("    </ul>")
        lines.append("  </div>")
    lines.append("</div>")
    return "\n".join(lines)


def _methodology(num: int, notes: list) -> str:
    lines = ['\n<div class="section">', '  <div class="section-header">',
             f'    <h2>{num}. Data Sources and Methodology</h2>', '  </div>', '', "  <ul>"]
    lines.extend(f"    <li>{escape(n)}</li>" for n in notes)
    lines.append("  </ul>\n</div>")
    return "\n".join(lines)


def generate(data: dict, domain: str, output_dir: str) -> dict:
    out = Path(output_dir)
    charts_dir = out / "charts"
    charts_dir.mkdir(parents=True, exist_ok=True)
    result = {"domain": domain, "files": [], "error": None}

    try:
        gr._require_chart_dependencies()
        gr._setup_matplotlib()
    except RuntimeError as exc:
        result["error"] = str(exc)
        return result

    chart_paths = {}
    for key, spec in data.get("charts", {}).items():
        chart_paths[key] = CHART_BUILDERS[spec["type"]](spec, charts_dir, f"monthly-{key}")
        chart_paths[key + ":caption"] = spec.get("caption", "")

    toc = [{"num": 1, "title": "Executive Summary", "subs": ["The month at a glance"]}]
    for i, sec in enumerate(data["sections"], 2):
        toc.append({"num": i, "title": escape(sec["heading"]), "subs": []})
    steps_num = len(data["sections"]) + 2
    toc.append({"num": steps_num, "title": "Next Steps", "subs": []})
    toc.append({"num": steps_num + 1, "title": "Data Sources and Methodology", "subs": []})

    body = [_title_page(data, domain), gr._build_toc(toc)]
    body.append(
        '\n<div class="section">\n  <div class="section-header">\n'
        '    <h2>1. Executive Summary</h2>\n  </div>\n\n'
        f'  <p>{escape(data["summary"])}</p>\n'
        f'{_cards(data.get("cards", []))}'
        + "".join(f'  <div class="success-box"><p>{escape(h)}</p></div>\n'
                  for h in data.get("highlights", []))
        + '</div>\n')
    fig = [0]
    for i, sec in enumerate(data["sections"], 2):
        body.append(_section(i, sec, chart_paths, fig))
    body.append(_next_steps(steps_num, data["next_steps"]))
    body.append(_methodology(steps_num + 1, data["methodology"]))

    html = (
        "<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n"
        f"<title>{escape(domain)} {escape(data['title'])} {escape(data['period'])}</title>\n"
        f"<style>\n{gr._build_css(domain)}\n</style>\n</head>\n<body>\n"
        + "".join(body) + "\n</body>\n</html>\n")

    html_path = out / "monthly-report.html"
    html_path.write_text(html, encoding="utf-8")
    if gr.HTML is None:
        result["error"] = "weasyprint is required for PDF generation"
        return result
    pdf_path = out / "monthly-report.pdf"
    try:
        gr.HTML(string=html).write_pdf(str(pdf_path))
    except Exception as exc:  # noqa: BLE001 - report the renderer error
        result["error"] = f"PDF generation failed: {exc}"
        return result
    result["files"] = [str(pdf_path)]
    result["review"] = gr._review_pdf(str(pdf_path), html)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Monthly SEO/AEO/GEO report generator")
    parser.add_argument("--data", required=True, help="Path to monthly report JSON")
    parser.add_argument("--domain", required=True, help="Domain for the header")
    parser.add_argument("--output-dir", default=".", help="Output directory")
    parser.add_argument("--json", action="store_true", help="Print result metadata as JSON")
    args = parser.parse_args()

    with open(args.data, encoding="utf-8") as handle:
        data = json.load(handle)
    result = generate(data, args.domain, args.output_dir)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(result.get("error") or "\n".join(result["files"]))
        if result.get("review"):
            print("review:", result["review"]["status"], result["review"]["issues"])
    ok = not result.get("error") and result.get("review", {}).get("status") == "PASS"
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
