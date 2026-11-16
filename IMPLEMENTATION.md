# Local CyberHull implementation

Source: https://github.com/AniketGhosal/CyberHull-URL-Detection
Imported revision: `4ce352b35ac89d6c670481d4cb97db273aae5ab9`.
The original notebooks, figures, mappings, and README are retained. The existing
local `origin` remote is preserved. The `cyberhull/` package is a new implementation
of the active algorithm in cells 0 and 1 of `notebooks/Auto_FGSH_Dynamic_Engine.ipynb`.

## Setup (PowerShell)

Python 3.13 is installed and a local `.venv` has been prepared. To recreate it:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e '.[test,notebooks]'
```

## Run the synthetic demonstration

```powershell
.\.venv\Scripts\python.exe examples/make_demo.py
New-Item -ItemType Directory -Force results/runs
.\.venv\Scripts\python.exe -m cyberhull train --data examples/demo_records.json --model results/runs/model.json --output results/runs/metrics.json
.\.venv\Scripts\python.exe -m cyberhull predict --data examples/demo_records.json --model results/runs/model.json --output results/runs/predictions.json
.\.venv\Scripts\python.exe -m pytest -q
```

Demo data is deliberately synthetic. Its results do not validate phishing detection
in the real world. Predictions include the one-based IDs of all violated vaults.

## Real dataset status (recovered)

Upstream `final_merged.json` is a 26,967,679-byte Git LFS object with SHA-256
`1a5275096c5f1130a2666a04e23ecc8542329c66cf50dd7fe063f90fddd372f4`.
The LFS batch download returned HTTP 404 during initial setup. The actual file was
subsequently recovered from GitHub's media endpoint and verified against that
SHA-256. `final_merged.json` now contains all 1,674 original records (204 legitimate
and 1,470 phishing), stored directly in Git rather than as an LFS pointer. The
explicit `-filter` attribute prevents inherited LFS rules from replacing it with
a pointer; `-text` preserves its exact checksum across platforms. Run:

```powershell
.\.venv\Scripts\python.exe -m cyberhull train --data final_merged.json --model results/runs/model.json
.\.venv\Scripts\python.exe -m cyberhull evaluate --data separate_labeled_records.json --model results/runs/model.json
.\.venv\Scripts\jupyter-lab.exe notebooks/Auto_FGSH_Dynamic_Engine.ipynb
```

Recovery source:
https://media.githubusercontent.com/media/AniketGhosal/CyberHull-URL-Detection/4ce352b35ac89d6c670481d4cb97db273aae5ab9/final_merged.json

To verify the local dataset in PowerShell:

```powershell
Get-FileHash final_merged.json -Algorithm SHA256
git check-attr filter -- final_merged.json
```

The hash must match the value above and `filter` must be `unset`. Add and push the
dataset using normal `git add`, `git commit`, and `git push`; no LFS upload or
history rewrite is needed. GitHub's browser upload limit is smaller than this file,
so use the Git CLI to upload it.

The notebook extras support the core and PCA notebooks. The exploratory collection
notebook has additional optional packages and Colab-specific cells; it is retained
as source material, not ported into the CLI.

## Input contract

Input is a JSON array of pre-extracted page records. Legacy comma-separated JSON
objects with a final trailing comma are also supported. Training/evaluation require
integer `status`: `1` means legitimate, `0` and `-1` mean phishing. Prediction does
not require labels. Fields follow the notebook:

```json
[{"main_url":"https://example.test", "main_domain":"example.test", "status":1,
  "main_entropy":3.2, "combined_entropy":3.4,
  "internal_pages":[{"entropy":3.1}], "external_links":[],
  "keyword_scores":{"login":0.2}}]
```

Missing measurements default to zero, as upstream. Supply real extracted page
features for meaningful inference: this is not a URL crawler and a bare URL is
insufficient to reconstruct entropy, semantic scores, or hyperlink topology.
Unknown prediction keywords are ignored; training fixes the keyword vocabulary.

## Algorithm and deliberate differences

- Extract seven structural features and up to 85 frequent keywords; remove constant
  features. The number of vaults depends on the training data, not a fixed 46.
- Greedily select globally strongest absolute-correlation pairs. Mutual information
  assigns the higher-scoring axis first. Stable tie-breaking and seed 42 make fits
  reproducible within the same dependency environment.
- For each pair, take the nearest 80% (including quantile ties) of legitimate points
  to the centroid in the original, unscaled feature coordinates, then build a hull.
- A record outside any vault is classified as phishing; this is a geometric anomaly
  decision rather than a calibrated probability or proof that a site is malicious.
- Replace upstream unseeded random jitter with affine-span geometry for collinear
  and identical points. Boundaries are included with a relative numerical tolerance.
  These changes mean outputs need not match the original notebook exactly.
- Fit vocabulary, feature selection, correlation, MI, and hulls only on the training
  split. Default evaluation uses a stratified 20% holdout and reports confusion counts,
  accuracy, phishing recall, and legitimate false-positive rate. It does not claim
  temporal, domain-disjoint, or zero-day validation.
- Save models as versioned JSON containing feature names and core points; no pickle
  execution is needed to load them.

The original dataset is now available. Local held-out evaluation is distinct from
the upstream notebook's in-sample results; it does not reproduce its accuracy claims.

## Local verification

The 13 automated tests pass, covering polygon, line and point boundaries, feature
extraction, repeatable fitting, JSON model round trips, frozen vocabulary, malformed
inputs, LFS pointer detection, and the train/predict/evaluate CLI workflow.
The default synthetic demo produces 160 training records, 40 held-out records,
eight active features and four vaults. Its holdout has 20 true positives, zero
false negatives, five true negatives and 15 false positives (75% false-positive
rate). This illustrates the strict any-vault rejection rule, not deployment quality.

With the recovered original dataset and the default seed, the CLI trains on 1,339
records with 91 active features and 46 vaults. The 335-record holdout yields 264
true positives, 30 false negatives, 10 true negatives and 31 false positives:
81.79% accuracy, 89.80% phishing recall, and 75.61% false-positive rate. This high
false-positive rate means the classifier is not ready for automatic blocking.
The fitted model and full metrics are saved locally under `results/runs/real-model.json`
and `results/runs/real-metrics.json`; these generated outputs are ignored by Git.
