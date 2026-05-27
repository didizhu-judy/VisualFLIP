# Third-Party Notices

VisualFLIP redistributes a small number of images derived from upstream sources.
This file collects their license texts and attribution requirements, as required
by those licenses. Their terms govern the corresponding subsets and override the
top-level `LICENSE` / `DATA_LICENSE` of this repository where applicable.

---

## MathVision (Wang et al., 2024)

**Scope of use in VisualFLIP.** 172 image pairs in the dataset are derived from
the [MathVision benchmark](https://github.com/mathllm/MATH-V) — the rows in
`manifest.jsonl` (and `data/manifest.jsonl`) where `source == "real_mathvision"`.

For each such pair the **original image** is the un-edited MathVision image as
distributed by the upstream repository, and the **edited image** is a derivative
work created by us that minimally alters the task-critical visual evidence so
the gold answer flips. The accompanying question text is also from MathVision.

**Attribution.** If you use the `source == "real_mathvision"` subset, please
also cite:

> Wang et al. *Measuring Multimodal Mathematical Reasoning with MATH-Vision
> Dataset.* 2024.

**License of the upstream MathVision dataset (verbatim copy, retrieved
2026-05-27 from <https://raw.githubusercontent.com/mathllm/MATH-V/main/LICENSE>):**

```
MIT License

Copyright (c) 2021 Dan Hendrycks

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

**Upstream provenance note.** MathVision itself notes that its problems are
collected from publicly available mathematics competitions. We have not
re-collected from those primary sources; we re-use what MathVision distributed
under MIT. Users who require stricter rights clearance on the underlying
competition material should consult the MathVision repository directly.

**How to filter out the MathVision subset.** If your downstream use has
stricter licensing requirements than MIT, restrict to the synthetic subset:

```python
import json
with open("manifest.jsonl") as f:
    synthetic_only = [json.loads(l) for l in f
                       if json.loads(l)["source"] == "synthetic"]   # 515 pairs
```

---

## Project page template (LLaVA-OneVision-2)

`docs/index.html`, `docs/static/css/styles.css`, `docs/static/js/main.js`, and
`docs/static/favicon.svg` are structurally adapted from the
[LLaVA-OneVision-2 project page](https://evolvinglmms-lab.github.io/LLaVA-OneVision-2/)
(source: <https://github.com/EvolvingLMMs-Lab/LLaVA-OneVision-2>), distributed
under the **Apache License 2.0**. The CSS and JS are vendored verbatim with a
single rename (the theme `localStorage` key changed from
`llava-onevision-2-theme` → `visualflip-theme`). HTML structure is adapted; all
content text is original to VisualFLIP.

> EvolvingLMMs-Lab. *LLaVA-OneVision-2: Towards Next-Generation Perceptual
> Intelligence.* 2026.

The upstream Apache-2.0 LICENSE (retrieved 2026-05-27 from
<https://raw.githubusercontent.com/EvolvingLMMs-Lab/LLaVA-OneVision-2/main/LICENSE>)
applies to the vendored CSS/JS/SVG. See that file for the full text.

---

## Synthetic subset (own work)

The 515 pairs with `source == "synthetic"` and the
**generation code under `synthetic_pairs/`** in the originating research
codebase are our own work, released under the licenses stated in `LICENSE`
(code, MIT) and `DATA_LICENSE` (data, CC BY 4.0).
