"""Train, evaluate, and classify pre-extracted URL feature records."""
import argparse
import json
from pathlib import Path

import numpy as np
from sklearn.metrics import confusion_matrix
from sklearn.model_selection import train_test_split

from .data import labels, load_records
from .model import CyberHull


def evaluate(model, records):
    actual = labels(records)
    predicted = np.array([r["prediction"] == "Phishing" for r in model.predict(records)], dtype=int)
    tn, fp, fn, tp = confusion_matrix(actual, predicted, labels=[0, 1]).ravel()
    return {"records": len(records), "true_negative": int(tn), "false_positive": int(fp),
            "false_negative": int(fn), "true_positive": int(tp),
            "accuracy": float(np.mean(actual == predicted)),
            "phishing_recall": float(tp / (tp + fn)) if tp + fn else None,
            "false_positive_rate": float(fp / (fp + tn)) if fp + tn else None}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    train = commands.add_parser("train", help="Fit on a stratified training split and report held-out metrics")
    train.add_argument("--data", required=True)
    train.add_argument("--model", required=True)
    train.add_argument("--core-fraction", type=float, default=0.8)
    train.add_argument("--test-size", type=float, default=0.2)
    train.add_argument("--seed", type=int, default=42)
    for name in ("predict", "evaluate"):
        command = commands.add_parser(name)
        command.add_argument("--data", required=True)
        command.add_argument("--model", required=True)
    for command in (train, *[commands.choices[n] for n in ("predict", "evaluate")]):
        command.add_argument("--output", help="Also write JSON results to this file")
    args = parser.parse_args(argv)
    try:
        records = load_records(args.data)
        if args.command == "train":
            if not 0 < args.test_size < 1:
                raise ValueError("test-size must be in (0, 1).")
            training, testing = train_test_split(records, test_size=args.test_size,
                                                random_state=args.seed, stratify=labels(records))
            model = CyberHull(args.core_fraction, seed=args.seed).fit(training)
            result = {"training_records": len(training), "features": len(model.features),
                      "vaults": len(model.vaults), "held_out": evaluate(model, testing)}
            model.save(args.model)
        else:
            model = CyberHull.load(args.model)
            result = model.predict(records) if args.command == "predict" else evaluate(model, records)
        text = json.dumps(result, indent=2, allow_nan=False)
        if args.output:
            Path(args.output).write_text(text + "\n", encoding="utf-8")
        print(text)
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(2, f"cyberhull: {error}\n")
