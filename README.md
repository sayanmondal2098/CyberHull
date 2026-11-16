# CyberHull: Deterministic Malicious URL Isolation via Convex Hull Geometry

**Local runnable implementation:** see [IMPLEMENTATION.md](IMPLEMENTATION.md) for
setup, CLI commands, tests, and dataset recovery details. The verified original
`data/final_merged.json` is included directly in Git; Git LFS is not required for it.
For download instructions and checksum verification, see [data/README.md](data/README.md).

## Run everything from one file

From PowerShell in the project folder:

```powershell
.\.venv\Scripts\python.exe run_all.py --test
```

This trains the model, evaluates a held-out split, saves predictions and a vault
mapping, generates a confusion-matrix plot, and runs the automated tests.
Results go to `results/runs/latest/`. Rerunning replaces the files in that folder.
Use `--output results/runs/experiment-2` to keep a separate run.

To regenerate all model visualizations as well:

```powershell
.\.venv\Scripts\python.exe run_all.py --all-images --test
```

Open `results/runs/latest/images/` for individual vault plots, the complete vault
matrix, top vaults, rejection counts, 2D/3D PCA plots, and `interactive_3d.html`.
The current dataset produces 51 PNGs there, plus the interactive HTML. The
confusion matrix remains in `results/runs/latest/confusion_matrix.png`.
These are new plots of the current run, not pixel-for-pixel reproductions of the
historical reference figures. PCA is a visualization, not a classification boundary.

First-time setup:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e '.[test,notebooks]'
```

This runs the packaged pipeline. The exploratory notebooks remain separate
interactive analyses; the runner does not execute their installation cells,
widgets, or Colab-specific code.

## Project layout

- `cyberhull/`: Python package and CLI.
- `run_all.py`: single-file entry point for the complete packaged pipeline.
- `notebooks/`: original research notebooks with project-relative input/output paths.
- `results/reference/`: upstream plots, HTML visualization, and mapping tables.
- `results/runs/`: local trained models, metrics, and predictions (Git-ignored).
- `results/generated/`: notebook outputs (Git-ignored).
- `docs/`: original pipeline document.
- `examples/` and `tests/`: synthetic demo generator and automated checks.
- `data/final_merged.json`: verified original dataset.

Welcome to the official repository for **CyberHull**, a multidimensional geometric threat-isolation framework. This repository contains the data and algorithmic implementations evaluated in our research.

## 📌 Repository Contents
* **`data/final_merged.json`**: The curated benchmarking dataset containing legitimate and zero-day phishing URL features.
* **`notebooks/Auto_FGSH_Dynamic_Engine.ipynb`**: The core Jupyter Notebook containing the Convex Hull boundary generation, optimization, and point-in-polyhedron testing logic.
* **`notebooks/PCA_Algorithm_Features.ipynb`**: The script used to generate the baseline Principal Component Analysis (PCA) comparison.
* **Visualizations & Proofs**: High-resolution 2D and 3D topographical visualizations of the geometric interception vaults (`.png` and `.html` formats).

## 🚀 Overview
Traditional probabilistic machine learning models struggle with the non-linear, structurally adaptive nature of modern phishing attacks. CyberHull addresses this by mapping high-variance web attributes (structural entropy, semantic keyword distribution, and hyperlink topology) into a multidimensional coordinate system. Using the QuickHull algorithm, it constructs mathematically rigorous, deterministic "Safe Zones."

## ⚙️ Requirements
To execute the notebooks, ensure you have the following dependencies installed:
`pip install pandas numpy scikit-learn scipy matplotlib plotly`
