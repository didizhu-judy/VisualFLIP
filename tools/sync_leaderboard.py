#!/usr/bin/env python3
"""
VisualFLIP — regenerate the leaderboard tables in README.md and docs/index.html
from a single source of truth (data/leaderboard.json).

By default, runs in CHECK mode (fails non-zero if README/docs are out of sync).
Pass --write to actually update the files. CI should use --check.

Usage
-----
  python tools/sync_leaderboard.py            # check only (default)
  python tools/sync_leaderboard.py --write    # regenerate README + docs blocks
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LB_JSON = ROOT / "data" / "leaderboard.json"
README = ROOT / "README.md"
INDEX_HTML = ROOT / "docs" / "index.html"

# README block markers — sync only what's between these.
README_START = "<!-- LEADERBOARD:START -->"
README_END = "<!-- LEADERBOARD:END -->"

INDEX_START = "<!-- LEADERBOARD:START -->"
INDEX_END = "<!-- LEADERBOARD:END -->"


def best_in(rows: list[dict], key: str, lower_is_better: bool) -> float:
    vals = [r[key] for r in rows]
    return min(vals) if lower_is_better else max(vals)


def render_readme_top10(rows: list[dict]) -> str:
    """Top-10 by avg_accp, ties broken by lower avg_cr."""
    ranked = sorted(rows, key=lambda r: (-r["avg_accp"], r["avg_cr"]))[:10]
    best_acc = best_in(rows, "avg_accp", lower_is_better=False)
    best_cr = best_in(rows, "avg_cr", lower_is_better=True)
    out = [
        "| # | Model | Year | Acc<sub>p</sub> ↑ | CR ↓ |",
        "|---:|---|---:|---:|---:|",
    ]
    for i, r in enumerate(ranked, 1):
        acc = f"{r['avg_accp']:.1f}"
        cr = f"{r['avg_cr']:.1f}"
        acc_md = f"**{acc}**" if r["avg_accp"] == best_acc else acc
        cr_md = f"**{cr}**" if r["avg_cr"] == best_cr else cr
        out.append(f"| {i} | {r['model']} | {r['year']} | {acc_md} | {cr_md} |")
    out.append("| … | (full table on project page) | | | |")
    return "\n".join(out)


GROUP_TAG = {
    "Closed-Source": "Closed",
    "Open-Source": "Open",
    "Open-Source, Tool-Augmented": "Tool-aug.",
}


def render_index_table(rows: list[dict]) -> str:
    """Full 24-row table for docs/index.html, grouped + best-in-column bolded."""
    best_acc_avg = best_in(rows, "avg_accp", lower_is_better=False)
    best_cr_avg = best_in(rows, "avg_cr", lower_is_better=True)

    groups: dict[str, list[dict]] = {"Closed-Source": [], "Open-Source": [],
                                     "Open-Source, Tool-Augmented": []}
    for r in rows:
        groups.setdefault(r["group"], []).append(r)
    for g in groups:
        groups[g].sort(key=lambda r: (-r["avg_accp"], r["avg_cr"]))

    out = []
    for grp in ["Closed-Source", "Open-Source", "Open-Source, Tool-Augmented"]:
        tag = GROUP_TAG[grp]
        for r in groups[grp]:
            cells = []
            for key, lower in [
                ("avg_accp", False), ("avg_cr", True),
                ("cardinality_accp", False), ("cardinality_cr", True),
                ("attribute_accp", False), ("attribute_cr", True),
                ("spatial_accp", False), ("spatial_cr", True),
                ("logic_accp", False), ("logic_cr", True),
            ]:
                v = r[key]
                txt = f"{v:.1f}"
                # Bold only the global best in the avg columns (matches existing styling).
                if key == "avg_accp" and v == best_acc_avg:
                    txt = f"<strong>{txt}</strong>"
                elif key == "avg_cr" and v == best_cr_avg:
                    txt = f"<strong>{txt}</strong>"
                cells.append(txt)
            cell_str = "".join(f"<td>{c}</td>" for c in cells)
            out.append(
                f"          <tr><td>{tag}</td><td>{r['model']}</td>"
                f"<td>{r['year']}</td>{cell_str}</tr>"
            )
    return "\n".join(out)


def replace_block(text: str, start: str, end: str, new_block: str) -> str:
    pattern = re.compile(re.escape(start) + r".*?" + re.escape(end), re.S)
    repl = f"{start}\n{new_block}\n{end}"
    if not pattern.search(text):
        raise SystemExit(
            f"ERROR: marker pair {start} ... {end} not found. "
            f"Wrap the table block with these comments first."
        )
    return pattern.sub(repl, text)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true",
                    help="Write changes to disk (default: check only, exit 1 on drift).")
    args = ap.parse_args()

    data = json.loads(LB_JSON.read_text())
    rows = data["rows"]

    readme_table = render_readme_top10(rows)
    index_table = render_index_table(rows)

    readme_text = README.read_text()
    index_text = INDEX_HTML.read_text()

    new_readme = replace_block(readme_text, README_START, README_END, readme_table)
    new_index = replace_block(index_text, INDEX_START, INDEX_END, index_table)

    changed = []
    if new_readme != readme_text:
        changed.append("README.md")
    if new_index != index_text:
        changed.append("docs/index.html")

    if not changed:
        print("OK: leaderboard tables in README.md and docs/index.html are in sync with "
              f"{LB_JSON.relative_to(ROOT)}")
        return

    if not args.write:
        print(f"DRIFT: out of sync: {', '.join(changed)}. Run with --write to fix.")
        sys.exit(1)

    if "README.md" in changed:
        README.write_text(new_readme)
        print(f"wrote {README}")
    if "docs/index.html" in changed:
        INDEX_HTML.write_text(new_index)
        print(f"wrote {INDEX_HTML}")


if __name__ == "__main__":
    main()
