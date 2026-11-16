"""Run training, held-out evaluation, predictions, plots, and optional tests."""
import argparse
import csv
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent


def run(data, output, seed=42, test_size=0.2, core_fraction=0.8, all_images=False):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    from sklearn.model_selection import train_test_split
    from cyberhull import CyberHull
    from cyberhull.cli import evaluate
    from cyberhull.data import labels, load_records

    records = load_records(data)
    training, testing = train_test_split(records, test_size=test_size,
                                        random_state=seed, stratify=labels(records))
    model = CyberHull(core_fraction=core_fraction, seed=seed).fit(training)
    output.mkdir(parents=True, exist_ok=True)
    model.save(output / "model.json")
    # Exercise the persisted model rather than only its in-memory counterpart.
    model = CyberHull.load(output / "model.json")
    metrics = evaluate(model, testing)
    report = {"dataset": str(data), "seed": seed, "core_fraction": core_fraction,
              "test_size": test_size, "training_records": len(training),
              "features": len(model.features), "vaults": len(model.vaults), "held_out": metrics}
    for filename, payload in (("metrics.json", report),
                              ("predictions.json", model.predict(records)),
                              ("held_out_predictions.json", model.predict(testing))):
        (output / filename).write_text(json.dumps(payload, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    with (output / "vault_mapping.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["vault", "anchor", "support", "core_points", "affine_rank"])
        for i, vault in enumerate(model.vaults, 1):
            writer.writerow([i, *vault.features, len(vault.points), vault.rank])

    matrix = np.array([[metrics["true_negative"], metrics["false_positive"]],
                       [metrics["false_negative"], metrics["true_positive"]]])
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.imshow(matrix, cmap="Blues")
    for (row, col), value in np.ndenumerate(matrix):
        ax.text(col, row, str(value), ha="center", va="center",
                color="white" if value > matrix.max() / 2 else "black", fontsize=18)
    ax.set(xticks=[0, 1], yticks=[0, 1], xticklabels=["Legitimate", "Phishing"],
           yticklabels=["Legitimate", "Phishing"], xlabel="Predicted class",
           ylabel="Actual class", title="CyberHull held-out confusion matrix")
    fig.tight_layout()
    fig.savefig(output / "confusion_matrix.png", dpi=160)
    plt.close(fig)
    if all_images:
        from cyberhull.plots import generate_images
        files = generate_images(model, training, testing, output / "images")
        print(f"Generated {len(files)} visualization files in {output / 'images'}", flush=True)
    print(json.dumps(report, indent=2))
    print(f"\nResults saved to {output}")
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=ROOT / "data/final_merged.json")
    parser.add_argument("--output", type=Path, default=ROOT / "results/runs/latest")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--core-fraction", type=float, default=0.8)
    parser.add_argument("--test", action="store_true", help="Run the automated test suite after the pipeline")
    parser.add_argument("--all-images", action="store_true", help="Generate every vault plot, summary plots, PCA plots, and interactive 3D HTML")
    args = parser.parse_args(argv)
    try:
        if not 0 < args.test_size < 1:
            raise ValueError("test-size must be in (0, 1).")
        run(args.data.resolve(), args.output.resolve(), args.seed, args.test_size, args.core_fraction, args.all_images)
        if args.test:
            subprocess.run([sys.executable, "-m", "pytest", "-q"], cwd=ROOT, check=True)
    except ImportError as error:
        parser.exit(2, f"Missing dependency: {error}. Install with: python -m pip install -e \".[test,notebooks]\"\n")
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        parser.exit(2, f"Pipeline failed: {error}\n")


if __name__ == "__main__":
    main()
