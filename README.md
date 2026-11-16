# CyberHull: Deterministic Malicious URL Isolation via Convex Hull Geometry

**Local runnable implementation:** see [IMPLEMENTATION.md](IMPLEMENTATION.md) for
setup, CLI commands, tests, and dataset recovery details. The verified original
`final_merged.json` is included directly in Git; Git LFS is not required for it.

Welcome to the official repository for **CyberHull**, a multidimensional geometric threat-isolation framework. This repository contains the data and algorithmic implementations evaluated in our research.

## 📌 Repository Contents
* **`final_merged.json`**: The curated benchmarking dataset containing legitimate and zero-day phishing URL features.
* **`Auto_FGSH_Dynamic_Engine.ipynb`**: The core Jupyter Notebook containing the Convex Hull boundary generation, optimization, and point-in-polyhedron testing logic.
* **`PCA_Algorithm_Features.ipynb`**: The script used to generate the baseline Principal Component Analysis (PCA) comparison.
* **Visualizations & Proofs**: High-resolution 2D and 3D topographical visualizations of the geometric interception vaults (`.png` and `.html` formats).

## 🚀 Overview
Traditional probabilistic machine learning models struggle with the non-linear, structurally adaptive nature of modern phishing attacks. CyberHull addresses this by mapping high-variance web attributes (structural entropy, semantic keyword distribution, and hyperlink topology) into a multidimensional coordinate system. Using the QuickHull algorithm, it constructs mathematically rigorous, deterministic "Safe Zones."

## ⚙️ Requirements
To execute the notebooks, ensure you have the following dependencies installed:
`pip install pandas numpy scikit-learn scipy matplotlib plotly`
