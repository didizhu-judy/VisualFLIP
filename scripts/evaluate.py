#!/usr/bin/env python3
"""
VisualFLIP — evaluation driver (OpenRouter).

Independent-mode evaluator over the VisualFLIP paired benchmark. For each row
in `manifest.jsonl` the same question is asked on `original_image` and on
`edited_image` as TWO SEPARATE chat completions (no shared context). Optionally
also evaluates the `irrelevant_image` arm for the 3 control templates.

Writes a per-pair results JSON that `aggregate.py` consumes to report
pair accuracy (Acc_p) and Collapse Rate (CR).

Usage
-----
  # 1) point at any local copy of the data (see `download_data.py`):
  export VISUALFLIP_DATA=/path/to/visualflip/data

  # 2) set your OpenRouter key (https://openrouter.ai):
  export OPENROUTER_API_KEY=sk-or-...

  # 3) run on a single model:
  python evaluate.py --model google/gemini-2.5-flash \\
      --manifest $VISUALFLIP_DATA/manifest.jsonl \\
      --data-root $VISUALFLIP_DATA \\
      --out results/gemini25flash.json

  # weak models: skip the two long-context templates
  python evaluate.py --model qwen/qwen2.5-vl-7b-instruct \\
      --exclude-templates color_connectivity,maze_path \\
      --max-tokens 2048 \\
      --out results/qwen25vl7b.json
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import requests

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
PROMPT_TEMPLATE = (
    "Think step by step. Put your reasoning in <thinking></thinking> and ONLY "
    "the final answer in <answer></answer>. Question: {question}"
)
ANSWER_RE = re.compile(r"<answer>\s*(.+?)\s*</answer>", re.IGNORECASE | re.DOTALL)
BOXED_RE = re.compile(r"\\boxed\{\s*([^{}]+?)\s*\}")
TRAILING_LETTER_RE = re.compile(r"\b([A-E])\b\s*\.?\s*$")
TRAILING_INT_RE = re.compile(r"(-?\d+)\s*\.?\s*$")
LONG_CONTEXT_TEMPLATES = {"color_connectivity", "maze_path"}


def encode_image(path: Path) -> str:
    with path.open("rb") as f:
        data = base64.b64encode(f.read()).decode("ascii")
    return f"data:image/png;base64,{data}"


def extract_answer(text: str) -> str:
    """Pull the final answer from a model response. Empty string if not found."""
    if not text:
        return ""
    m = ANSWER_RE.search(text)
    if m:
        return m.group(1).strip()
    m = BOXED_RE.search(text)
    if m:
        return m.group(1).strip()
    tail = text.strip().splitlines()[-1] if text.strip() else ""
    m = TRAILING_LETTER_RE.search(tail)
    if m:
        return m.group(1).upper()
    m = TRAILING_INT_RE.search(tail)
    if m:
        return m.group(1)
    return ""


def normalize(s: Any) -> str:
    return str(s).strip().upper()


def call_openrouter(
    model: str,
    api_key: str,
    image_data_url: str,
    question: str,
    max_tokens: int,
    temperature: float,
    timeout: int = 180,
) -> tuple[str, str | None]:
    """Returns (text, finish_reason)."""
    body = {
        "model": model,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": image_data_url}},
                    {"type": "text", "text": PROMPT_TEMPLATE.format(question=question)},
                ],
            }
        ],
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/didizhu-judy/VisualFLIP",
        "X-Title": "VisualFLIP eval",
    }
    last_err: Exception | None = None
    for attempt in range(3):
        try:
            r = requests.post(OPENROUTER_URL, headers=headers, json=body, timeout=timeout)
            r.raise_for_status()
            j = r.json()
            choice = j["choices"][0]
            text = choice["message"].get("content") or ""
            return text, choice.get("finish_reason")
        except Exception as e:  # noqa: BLE001
            last_err = e
            time.sleep(2 + 2 * attempt)
    raise RuntimeError(f"OpenRouter call failed after 3 attempts: {last_err}")


def eval_arm(model: str, api_key: str, image_path: Path, question: str, max_tokens: int,
             temperature: float, strict_truncation: bool = False):
    img = encode_image(image_path)
    text, finish = call_openrouter(model, api_key, img, question, max_tokens, temperature)
    pred = extract_answer(text)
    # Truncation handling. Two policies:
    #   default        — invalidate ONLY if response was cut off before <answer> appeared.
    #                    A completed <answer>X</answer> that happened to truncate AFTER
    #                    counts as X.
    #   --strict-truncation — invalidate ANY response with finish_reason == "length".
    has_answer_tag = bool(ANSWER_RE.search(text or ""))
    truncated = (finish == "length") and (strict_truncation or not has_answer_tag)
    if truncated:
        pred = ""
    return {"text": text, "pred": pred, "truncated": truncated, "finish_reason": finish}


def eval_pair(model, api_key, rec, data_root: Path, max_tokens: int, temperature: float,
              strict_truncation: bool = False):
    q = rec["question"]
    out: dict[str, Any] = {
        "pair_dir": rec["id"],
        "id": rec["id"],
        "source": rec["source"],
        "category": rec["category"],
        "template": rec.get("template"),
        "question": q,
        "answer_original": rec["answer_original"],
        "answer_edited": rec["answer_edited"],
    }
    # Per-template long-context override.
    tmpl_max = max(max_tokens, 8192) if rec.get("template") in LONG_CONTEXT_TEMPLATES else max_tokens

    o = eval_arm(model, api_key, data_root / rec["original_image"], q, tmpl_max, temperature, strict_truncation)
    e = eval_arm(model, api_key, data_root / rec["edited_image"], q, tmpl_max, temperature, strict_truncation)
    out["pred_original"] = o["pred"]
    out["pred_edited"] = e["pred"]
    out["raw_original"] = o["text"]
    out["raw_edited"] = e["text"]
    out["truncated_o"] = o["truncated"]
    out["truncated_e"] = e["truncated"]

    ao, ae = normalize(rec["answer_original"]), normalize(rec["answer_edited"])
    po, pe = normalize(out["pred_original"]), normalize(out["pred_edited"])
    out["correct_original"] = bool(po and po == ao)
    out["correct_edited"] = bool(pe and pe == ae)
    out["inertia_flag"] = bool(po and po == pe)

    if rec.get("has_control"):
        c = eval_arm(model, api_key, data_root / rec["irrelevant_image"], q, tmpl_max, temperature, strict_truncation)
        out["pred_irrelevant"] = c["pred"]
        out["raw_irrelevant"] = c["text"]
        out["truncated_irr"] = c["truncated"]
        ai = normalize(rec["answer_irrelevant"])
        pi = normalize(c["pred"])
        out["correct_irrelevant"] = bool(pi and pi == ai)
    return out


def main():
    ap = argparse.ArgumentParser(description="VisualFLIP evaluator (OpenRouter, independent mode).")
    ap.add_argument("--model", required=True, help="OpenRouter model id, e.g. google/gemini-2.5-flash")
    ap.add_argument("--manifest", default=os.environ.get("VISUALFLIP_MANIFEST", "data/manifest.jsonl"))
    ap.add_argument("--data-root", default=os.environ.get("VISUALFLIP_DATA", "data"),
                    help="Directory image paths in manifest are relative to.")
    ap.add_argument("--out", required=True, help="Output JSON file (list of per-pair records).")
    ap.add_argument("--api-key", default=os.environ.get("OPENROUTER_API_KEY"))
    ap.add_argument("--max-tokens", type=int, default=4096,
                    help="Max new tokens; color_connectivity / maze_path auto-bump to 8192.")
    ap.add_argument("--temperature", type=float, default=0.0)
    ap.add_argument("--concurrency", type=int, default=6)
    ap.add_argument("--limit", type=int, default=None, help="Eval only the first N pairs (smoke test).")
    ap.add_argument("--include-templates", default=None,
                    help="Comma-separated template names to keep (default: all).")
    ap.add_argument("--exclude-templates", default=None,
                    help="Comma-separated template names to skip (use to drop long ones for weak models).")
    ap.add_argument("--include-source", default=None,
                    help="Restrict to one source: synthetic | real_mathvision")
    ap.add_argument("--resume", action="store_true",
                    help="Skip ids already present in --out (if it exists).")
    ap.add_argument("--allow-failures", action="store_true",
                    help="Continue after per-pair API failures (default: abort nonzero "
                         "if any pair fails). Use only for exploratory runs.")
    ap.add_argument("--strict-truncation", action="store_true",
                    help="Treat ANY response with finish_reason='length' as an empty "
                         "prediction, even if <answer>...</answer> was already emitted "
                         "before the cut-off. Default: only invalidate when the answer "
                         "tag is missing (more permissive; matches typical OpenAI-style "
                         "API behaviour).")
    args = ap.parse_args()

    if not args.api_key:
        print("ERROR: --api-key not given and OPENROUTER_API_KEY not in env.", file=sys.stderr)
        sys.exit(2)
    manifest_path = Path(args.manifest)
    data_root = Path(args.data_root)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    inc = set(s.strip() for s in args.include_templates.split(",")) if args.include_templates else None
    exc = set(s.strip() for s in args.exclude_templates.split(",")) if args.exclude_templates else set()

    records: list[dict[str, Any]] = []
    with manifest_path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            t = r.get("template")
            if inc is not None and t not in inc:
                continue
            if t in exc:
                continue
            if args.include_source and r.get("source") != args.include_source:
                continue
            records.append(r)
    if args.limit:
        records = records[: args.limit]

    done: dict[str, dict] = {}
    if args.resume and out_path.exists():
        try:
            done = {r["id"]: r for r in json.loads(out_path.read_text())}
            print(f"[resume] loaded {len(done)} done records from {out_path}", file=sys.stderr)
        except Exception as e:  # noqa: BLE001
            print(f"[resume] failed to load {out_path}: {e}", file=sys.stderr)
    todo = [r for r in records if r["id"] not in done]
    print(f"[plan] total={len(records)} done={len(done)} todo={len(todo)} model={args.model}", file=sys.stderr)

    results: list[dict] = list(done.values())
    t0 = time.time()
    failures = 0
    failed_ids: list[str] = []
    with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        futs = {
            pool.submit(eval_pair, args.model, args.api_key, r, data_root,
                        args.max_tokens, args.temperature, args.strict_truncation): r
            for r in todo
        }
        for i, fut in enumerate(as_completed(futs), 1):
            r = futs[fut]
            try:
                results.append(fut.result())
            except Exception as e:  # noqa: BLE001
                failures += 1
                failed_ids.append(r["id"])
                print(f"[fail {failures}] id={r['id']}: {e}", file=sys.stderr)
                continue
            if i % 25 == 0 or i == len(todo):
                # Atomic snapshot so a kill doesn't lose work.
                tmp = out_path.with_suffix(out_path.suffix + ".tmp")
                tmp.write_text(json.dumps(results, ensure_ascii=False))
                tmp.replace(out_path)
                elapsed = time.time() - t0
                rate = i / elapsed if elapsed else 0
                eta = (len(todo) - i) / rate if rate else 0
                print(f"[{i}/{len(todo)}]  fail={failures}  {rate:.2f} pair/s  eta {eta/60:.1f} min", file=sys.stderr)

    out_path.write_text(json.dumps(results, ensure_ascii=False, indent=2))
    print(f"[done] wrote {len(results)} records ({failures} failures) -> {out_path}", file=sys.stderr)

    if failures and not args.allow_failures:
        print(
            f"\nERROR: {failures} pair(s) failed to evaluate (e.g. {failed_ids[:5]}). "
            f"Results JSON contains {len(results)} of {len(records)} expected records. "
            f"Re-run with --resume to retry just the missing ids, or pass --allow-failures "
            f"to ignore (NOT recommended for official leaderboard submissions).",
            file=sys.stderr,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
