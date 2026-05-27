#!/usr/bin/env python3
"""
VisualFLIP — symmetric metric aggregator.

Reads per-pair JSON files produced by `evaluate.py` and prints, per-template /
per-category / overall:

  * Acc_p (pair accuracy)
        = #pairs where BOTH sides are correct / #pairs
    The strict, direction-free analog of accuracy on a paired benchmark.

  * Acc (single-image, symmetric)
        = D / (2N),  where D = sum over pairs of (correct_o + correct_e)
    Reported alongside as a sanity check.

  * CR (Collapse Rate, primary)
        = #pairs (competent on >=1 side AND pred_o == pred_e, non-empty)
          / #pairs (competent on >=1 side)
    Of the pairs the model could solve on at least one side, the fraction
    where it gave the SAME answer to both images despite the gold flipping.

  * U / I / O decomposition (appendix)
        U_sym = 2 * both_correct / D
        I_sym = collapsed_competent / D
        O_sym = 1 - U - I
    (U + I + O = 1 on the symmetric competence denominator D.)

  * Controls (3 templates with an `irrelevant_image` arm only):
        S = answer stayed despite an irrelevant edit (preservation, higher = better)
        F = answer flipped on an irrelevant edit (false-flip, lower = better)

  * real-MathVision only: the directional rho_inert (legacy) is also printed,
        because for real images the "original" vs "edited" label is genuine.

Usage
-----
  python aggregate.py results/gemini25flash.json
  python aggregate.py results/*.json --json summary.json
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

CONTROL_TEMPLATES = {"hard_dense_count", "attr_dense_color_count", "layer_order"}


def _safe_div(a: float, b: float) -> float:
    return (a / b) if b else 0.0


def compute_block(records: list[dict[str, Any]]) -> dict[str, Any]:
    n = len(records)
    if n == 0:
        return {}

    # Symmetric competence counts.
    co = sum(1 for r in records if r["correct_original"])
    ce = sum(1 for r in records if r["correct_edited"])
    both = sum(1 for r in records if r["correct_original"] and r["correct_edited"])
    competent_pairs = sum(1 for r in records if r["correct_original"] or r["correct_edited"])
    collapsed_competent = sum(
        1 for r in records
        if (r["correct_original"] or r["correct_edited"]) and r["inertia_flag"]
    )
    D = co + ce

    # Directional rho_inert (legacy; meaningful only for real_mathvision).
    rho_num = sum(1 for r in records if r["correct_original"] and r["inertia_flag"])
    rho_den = co

    block: dict[str, Any] = {
        "n_pairs": n,
        "acc_pair": _safe_div(both, n),                # both sides correct
        "acc_symmetric": _safe_div(D, 2 * n),         # avg side accuracy
        "CR": _safe_div(collapsed_competent, competent_pairs),
        "U_sym": _safe_div(2 * both, D),
        "I_sym": _safe_div(collapsed_competent, D),   # I_num is on the symmetric denom too
        "competent_pairs": competent_pairs,
        "co": co, "ce": ce, "both": both,
        "rho_inert_directional": _safe_div(rho_num, rho_den),
    }
    block["O_sym"] = max(0.0, 1.0 - block["U_sym"] - block["I_sym"])

    # Controls (subset of records).
    ctl = [r for r in records if "correct_irrelevant" in r]
    if ctl:
        s = sum(1 for r in ctl
                if r["correct_original"] and (r.get("pred_irrelevant", "") or "").strip().upper()
                == (r.get("pred_original", "") or "").strip().upper())
        f = sum(1 for r in ctl
                if r["correct_original"] and (r.get("pred_irrelevant", "") or "").strip().upper()
                != (r.get("pred_original", "") or "").strip().upper()
                and (r.get("pred_irrelevant", "") or ""))
        denom = sum(1 for r in ctl if r["correct_original"])
        block["control_preservation"] = _safe_div(s, denom)
        block["control_false_flip"] = _safe_div(f, denom)
        block["control_n"] = len(ctl)
    return block


def aggregate_one(records: list[dict[str, Any]]) -> dict[str, Any]:
    by_template: dict[str, list[dict]] = defaultdict(list)
    by_category: dict[str, list[dict]] = defaultdict(list)
    by_source: dict[str, list[dict]] = defaultdict(list)
    for r in records:
        by_template[r.get("template") or "real_mathvision"].append(r)
        by_category[r["category"]].append(r)
        by_source[r["source"]].append(r)

    return {
        "overall": compute_block(records),
        "by_source": {k: compute_block(v) for k, v in by_source.items()},
        "by_category": {k: compute_block(v) for k, v in by_category.items()},
        "by_template": {k: compute_block(v) for k, v in by_template.items()},
    }


def _fmt_row(name: str, b: dict[str, Any]) -> str:
    return (
        f"  {name:32s}  n={b['n_pairs']:>4d}  "
        f"Acc_p={b['acc_pair']*100:5.1f}  "
        f"Acc={b['acc_symmetric']*100:5.1f}  "
        f"CR={b['CR']*100:5.1f}  "
        f"U={b['U_sym']*100:5.1f}  I={b['I_sym']*100:5.1f}  O={b['O_sym']*100:5.1f}"
    )


def print_summary(label: str, agg: dict[str, Any]) -> None:
    print(f"\n=== {label} ===")
    o = agg["overall"]
    print(_fmt_row("OVERALL", o))
    print(f"      (competent_pairs = {o['competent_pairs']})")
    print("  -- by source --")
    for k, v in sorted(agg["by_source"].items()):
        print(_fmt_row(k, v))
        # Directional rho_inert is meaningful only for real_mathvision (the synthetic
        # subset's "original" vs "edited" labels are arbitrary, so direction is fake).
        if k == "real_mathvision":
            print(f"        rho_inert (directional, real only) = "
                  f"{v['rho_inert_directional']*100:.1f}")
    print("  -- by category --")
    for k, v in sorted(agg["by_category"].items()):
        print(_fmt_row(k, v))
    print("  -- by template --")
    for k, v in sorted(agg["by_template"].items()):
        print(_fmt_row(k, v))
        if k in CONTROL_TEMPLATES and "control_preservation" in v:
            print(f"        controls: S={v['control_preservation']*100:.1f}  "
                  f"F={v['control_false_flip']*100:.1f}  n_ctl={v['control_n']}")


REQUIRED_FIELDS = {"id", "source", "category", "correct_original", "correct_edited", "inertia_flag"}


def validate(path: Path, recs: list, expected_n: int | None) -> list[str]:
    """Return a list of validation error strings (empty = OK)."""
    errs: list[str] = []
    if expected_n is not None and len(recs) != expected_n:
        errs.append(f"n_pairs={len(recs)} but --expected-n={expected_n}")
    seen: set[str] = set()
    for i, r in enumerate(recs):
        if not isinstance(r, dict):
            errs.append(f"row {i}: not a dict")
            continue
        missing = REQUIRED_FIELDS - set(r)
        if missing:
            errs.append(f"row {i} (id={r.get('id')!r}): missing fields {sorted(missing)}")
        rid = r.get("id")
        if rid in seen:
            errs.append(f"duplicate id: {rid!r}")
        seen.add(rid)
    return errs


def main():
    ap = argparse.ArgumentParser(description="VisualFLIP metric aggregator.")
    ap.add_argument("results", nargs="+", help="One or more JSON files from evaluate.py")
    ap.add_argument("--json", default=None, help="Also dump machine-readable JSON summary here.")
    ap.add_argument("--expected-n", type=int, default=None,
                    help="If set, fail with nonzero exit when any input has != expected_n records "
                         "(e.g. --expected-n 687 for the full official benchmark).")
    args = ap.parse_args()

    summary: dict[str, dict] = {}
    any_validation_error = False
    for p in args.results:
        path = Path(p)
        try:
            recs = json.loads(path.read_text())
        except Exception as e:  # noqa: BLE001
            print(f"[skip] {path}: {e}")
            continue
        if not isinstance(recs, list):
            print(f"[skip] {path}: top-level must be a list of per-pair records")
            continue
        errs = validate(path, recs, args.expected_n)
        for e in errs:
            print(f"[!! {path.stem}] {e}", file=__import__("sys").stderr)
        if errs:
            any_validation_error = True
        agg = aggregate_one(recs)
        print_summary(path.stem, agg)
        summary[path.stem] = agg

    if args.json:
        Path(args.json).write_text(json.dumps(summary, indent=2))
        print(f"\n[wrote] {args.json}")

    if any_validation_error:
        import sys; sys.exit(2)


if __name__ == "__main__":
    main()
