#!/usr/bin/env python3
"""
VisualFLIP — one-command dataset pull from the Hugging Face Hub.

Mirrors `didizhu-judy/VisualFLIP` (manifest + all images) into a local dir and
prints the env vars you need to set so `evaluate.py` can find the data.

Usage
-----
  pip install -U huggingface_hub
  python download_data.py                 # default: ./visualflip_data
  python download_data.py --out /data/vf  # custom location
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

REPO_ID = "DidiZhu/VisualFLIP"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="./visualflip_data",
                    help="Local directory to mirror the dataset into.")
    ap.add_argument("--revision", default="main", help="HF revision / branch / tag.")
    ap.add_argument("--manifest-only", action="store_true",
                    help="Download just manifest.jsonl (no images, for smoke tests).")
    args = ap.parse_args()

    try:
        from huggingface_hub import snapshot_download, hf_hub_download
    except ImportError:
        print("ERROR: pip install -U huggingface_hub", file=sys.stderr)
        sys.exit(2)

    out = Path(args.out).expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)

    if args.manifest_only:
        path = hf_hub_download(repo_id=REPO_ID, filename="manifest.jsonl",
                               repo_type="dataset", revision=args.revision,
                               local_dir=str(out))
        print(f"\n[ok] manifest -> {path}")
    else:
        path = snapshot_download(repo_id=REPO_ID, repo_type="dataset",
                                 revision=args.revision, local_dir=str(out))
        print(f"\n[ok] dataset mirrored -> {path}")

    print("\nNow run evaluate.py with:")
    print(f"  export VISUALFLIP_DATA={out}")
    print(f"  export VISUALFLIP_MANIFEST={out}/manifest.jsonl")
    print(f"  export OPENROUTER_API_KEY=sk-or-...")
    print(f"  python evaluate.py --model google/gemini-2.5-flash \\")
    print(f"      --out results/gemini25flash.json")


if __name__ == "__main__":
    main()
