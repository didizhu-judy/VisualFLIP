# Contributing to VisualFLIP

Thanks for the interest! Two contribution paths are explicitly supported.

## 1. Submit a model to the leaderboard

We accept evaluations from anyone who follows the protocol exactly. The bar is: same
prompt, independent mode, same answer-extraction rules, truncation-as-invalid.

**To submit a result:**

1. Run the eval (or your own equivalent that matches the protocol — see
   [README §Evaluation protocol](README.md#evaluation-protocol-independent-mode)):

   ```bash
   python scripts/evaluate.py --model <openrouter/id-or-local-name> \
       --out results/<your-model>.json --max-tokens 8192
   python scripts/aggregate.py results/<your-model>.json --json summary/<your-model>.json
   ```

2. Open a PR adding **two files** to your fork:
   - `results/<your-model>.json` — the per-pair output of `evaluate.py`
   - `summary/<your-model>.json` — the aggregated metrics from `aggregate.py --json`

3. In the PR description, include:
   - Model name + version + how it was served (OpenRouter id, local checkpoint sha, …)
   - Generation params (max_tokens, temperature, any system prompt added)
   - Whether any templates were excluded and why
   - Eval date and total cost / wall-clock if known

4. Maintainer will spot-check ~20 pairs by re-running the model on those, then merge and
   update the leaderboard (`data/leaderboard.json` + project page).

**What we won't accept (without discussion first):**
- Results with a non-zero temperature or a custom system prompt that wasn't disclosed.
- Results that exclude templates for reasons other than the documented long-context limits.
- Results that re-derive metrics with a different denominator from `aggregate.py`.

## 2. Report a data issue

Open a GitHub issue with:
- The pair `id` (from `manifest.jsonl`)
- What's wrong (wrong gold answer, ambiguous question, broken image, …)
- A proposed fix if you have one

We re-release with a minor version bump and a `CHANGELOG.md` entry whenever pairs are
edited or removed. The HuggingFace dataset and `manifest.jsonl` always carry a version
in the YAML frontmatter / first line of the changelog.

## 3. Code contributions

Small, focused PRs welcome (bug fixes in the eval driver / aggregator / Space, doc
improvements, additional convenience flags). For anything larger — new metrics,
new templates, alternative eval modes — please open an issue first to discuss scope.

Code style: black + ruff defaults. The scripts are intentionally dependency-light
(`requests` + `huggingface_hub` is all you need to evaluate).

## License of contributions

By submitting a PR you agree to license your contribution under the project's licenses:
MIT for code, CC BY 4.0 for any data or annotation changes.
