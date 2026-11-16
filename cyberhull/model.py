"""Global correlation pairing, MI axis assignment, and 80% legitimate core hulls."""
import json
from itertools import combinations
from pathlib import Path

import numpy as np
from scipy.spatial import ConvexHull
from sklearn.feature_selection import mutual_info_classif

from .data import feature_frame, labels, vocabulary


class Vault:
    """Convex set in its affine span; exact line/point cases need no random jitter."""

    def __init__(self, features, points, core_fraction=1.0):
        self.features = list(features)
        points = np.asarray(points, dtype=float)
        distances = np.linalg.norm(points - points.mean(axis=0), axis=1)
        self.points = np.unique(points[distances <= np.quantile(distances, core_fraction)], axis=0)
        self.center = self.points.mean(axis=0)
        centered = self.points - self.center
        _, singular, basis = np.linalg.svd(centered, full_matrices=False)
        threshold = max(centered.shape) * np.finfo(float).eps * (singular[0] if len(singular) else 0)
        self.rank = int(np.sum(singular > threshold))
        self.basis = basis[:self.rank].T
        projected = centered @ self.basis
        self.tolerance = 1e-9 * max(1.0, float(np.abs(self.points).max()))
        if self.rank == 2:
            self.equations = ConvexHull(projected).equations
        elif self.rank == 1:
            self.low, self.high = projected.min(), projected.max()

    def contains(self, points):
        centered = np.asarray(points) - self.center
        projected = centered @ self.basis
        residual = centered - projected @ self.basis.T
        inside = np.linalg.norm(residual, axis=1) <= self.tolerance
        if self.rank == 2:
            inside &= np.all(projected @ self.equations[:, :-1].T + self.equations[:, -1]
                             <= self.tolerance, axis=1)
        elif self.rank == 1:
            inside &= (projected[:, 0] >= self.low - self.tolerance) & (projected[:, 0] <= self.high + self.tolerance)
        return inside


class CyberHull:
    def __init__(self, core_fraction=0.8, max_keywords=85, seed=42):
        if not 0 < core_fraction <= 1:
            raise ValueError("core_fraction must be in (0, 1].")
        if max_keywords < 0:
            raise ValueError("max_keywords must be nonnegative.")
        self.core_fraction, self.max_keywords, self.seed = core_fraction, max_keywords, seed
        self.vaults = []

    def fit(self, records):
        y = labels(records)
        if min(np.sum(y == 0), np.sum(y == 1)) < 4:
            raise ValueError("Training requires at least four legitimate and four phishing records.")
        # Validate all keyword scores before selecting the training vocabulary.
        for r in records:
            if not isinstance(r.get("keyword_scores") or {}, dict):
                raise ValueError("keyword_scores must be an object.")
        keywords = vocabulary(records, self.max_keywords)
        frame = feature_frame(records, keywords)
        active = frame.loc[:, frame.nunique() > 1]
        features = list(active.columns)
        if len(features) < 2:
            raise ValueError("Training requires at least two nonconstant features.")
        mi = dict(zip(features, mutual_info_classif(active, y, random_state=self.seed)))
        corr = active.corr().abs().fillna(0)
        pairs = sorted(combinations(features, 2), key=lambda p: (-corr.loc[p[0], p[1]], p))
        remaining = set(features)
        spaces = []
        for a, b in pairs:
            if a in remaining and b in remaining:
                spaces.append(sorted([a, b], key=lambda f: (-mi[f], f)))
                remaining.difference_update([a, b])
        if remaining:
            a = next(iter(remaining))
            b = min((f for f in features if f != a), key=lambda f: (-corr.loc[a, f], f))
            spaces.append(sorted([a, b], key=lambda f: (-mi[f], f)))
        vaults = [Vault(pair, frame.loc[y == 0, pair].to_numpy(), self.core_fraction) for pair in spaces]
        self.keywords, self.features, self.vaults = keywords, features, vaults
        return self

    def predict(self, records):
        if not self.vaults:
            raise ValueError("Fit or load a model before prediction.")
        frame = feature_frame(records, self.keywords)
        outside = np.column_stack([~v.contains(frame[v.features].to_numpy()) for v in self.vaults])
        return [{"main_url": r.get("main_url", ""),
                 "prediction": "Phishing" if row.any() else "Legitimate",
                 "outside_vaults": [i + 1 for i, value in enumerate(row) if value]}
                for r, row in zip(records, outside)]

    def save(self, path):
        if not self.vaults:
            raise ValueError("Cannot save an unfitted model.")
        payload = {"format_version": 1, "core_fraction": self.core_fraction,
                   "max_keywords": self.max_keywords, "seed": self.seed,
                   "keywords": self.keywords, "features": self.features,
                   "vaults": [{"features": v.features, "points": v.points.tolist()} for v in self.vaults]}
        Path(path).write_text(json.dumps(payload, indent=2, allow_nan=False), encoding="utf-8")

    @classmethod
    def load(cls, path):
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        if data.get("format_version") != 1:
            raise ValueError("Unsupported model format version.")
        model = cls(data["core_fraction"], data["max_keywords"], data["seed"])
        model.keywords, model.features = data["keywords"], data["features"]
        model.vaults = [Vault(v["features"], v["points"]) for v in data["vaults"]]
        if not model.vaults:
            raise ValueError("Model contains no vaults.")
        return model
