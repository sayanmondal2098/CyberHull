"""Load the upstream record format and freeze training-time keyword features."""
import json
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

BASE_FEATURES = ["main_entropy", "combined_entropy", "url_length", "domain_length",
                 "n_internal_pages", "n_external_links", "avg_internal_entropy"]


def load_records(path):
    text = Path(path).read_text(encoding="utf-8-sig").strip()
    if text.startswith("version https://git-lfs.github.com/spec/v1"):
        raise ValueError(f"{path} is a Git LFS pointer, not a dataset. Obtain the actual "
                         "final_merged.json from the upstream author or supply another dataset.")
    text = text.rstrip(",").strip()
    records = json.loads(text if text.startswith("[") else f"[{text}]")
    if not records or not all(isinstance(r, dict) for r in records):
        raise ValueError("Input must contain a nonempty JSON list of record objects.")
    return records


def labels(records):
    if any(type(r.get("status")) is not int or r["status"] not in (-1, 0, 1) for r in records):
        raise ValueError("Every training/evaluation record needs status 1 (legitimate), 0 or -1 (phishing).")
    return np.array([0 if r["status"] == 1 else 1 for r in records])


def vocabulary(records, limit=85):
    counts = Counter(k for r in records for k in (r.get("keyword_scores") or {}))
    return sorted(counts, key=lambda k: (-counts[k], k))[:limit]


def feature_frame(records, keywords):
    rows = []
    for index, r in enumerate(records):
        try:
            pages = r.get("internal_pages") or []
            links = r.get("external_links") or []
            scores = r.get("keyword_scores") or {}
            if not isinstance(pages, list) or not isinstance(links, list) or not isinstance(scores, dict):
                raise ValueError("pages and links must be lists; keyword_scores must be an object")
            entropies = [p["entropy"] for p in pages if isinstance(p, dict)
                         and isinstance(p.get("entropy"), (int, float))]
            values = [float(r.get("main_entropy") or 0), float(r.get("combined_entropy") or 0),
                      len(str(r.get("main_url") or "")), len(str(r.get("main_domain") or "")),
                      len(pages), len(links), float(np.mean(entropies)) if entropies else 0.0]
            values += [float(scores.get(k) or 0) for k in keywords]
            if not np.isfinite(values).all():
                raise ValueError("feature values must be finite")
            rows.append(values)
        except (TypeError, ValueError) as error:
            raise ValueError(f"Invalid features in record {index}: {error}") from error
    return pd.DataFrame(rows, columns=BASE_FEATURES + [f"kw_{k}" for k in keywords])
