# Changelog

All notable changes to VisualFLIP are documented here. Versions follow
[Semantic Versioning](https://semver.org/) (MAJOR.MINOR.PATCH). The dataset
version is tagged on both the GitHub repo and the Hugging Face dataset.

## [1.0.0] — 2026-05-27

First public release.

### Dataset

- **687 paired image-flips** = 515 synthetic + 172 real-image (MathVision derived).
- **4 perturbation categories**: Cardinality (146), Attribute (273), Spatial (150), Logic (118).
- **14 templates** = 13 synthetic generators + 1 real-image set.
- **140 of 687 pairs** ship an additional `irrelevant_image` control arm
  (templates: `hard_dense_count`, `attr_dense_color_count`, `layer_order`).
- **1,514 PNGs** total (1,374 paired + 140 control), ~530 MB on Hugging Face.

### Code

- `scripts/evaluate.py` — OpenRouter eval driver, independent mode.
- `scripts/aggregate.py` — symmetric metric aggregator (Acc<sub>p</sub> / CR / U-I-O / controls).
- `scripts/download_data.py` — one-command HF snapshot pull.
- `tools/sync_leaderboard.py` — regenerate README/docs tables from `data/leaderboard.json`.

### Metrics

- **Acc<sub>p</sub>** (pair accuracy) and **Collapse Rate (CR)** are the primary metrics.
- The legacy directional `rho_inert` from earlier paper drafts is still printed by
  `aggregate.py` for the real-image subset only (where direction is meaningful);
  it is **not** combined with the symmetric CR.

### Leaderboard

- 24 MLLMs reported in `data/leaderboard.json`, sourced verbatim from the paper's
  Table 1. The same table is rendered into `README.md` (top-10) and `docs/index.html`
  (full 24).

### Licensing

- **Code:** MIT (see `LICENSE`).
- **Synthetic data (515 pairs):** CC BY 4.0 (see `DATA_LICENSE`).
- **Real-image data (172 pairs):** MIT, inherited from upstream MathVision
  (see `THIRD_PARTY_NOTICES.md`).
