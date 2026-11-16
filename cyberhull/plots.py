"""Regenerate plots from the fitted model and its actual held-out records."""
import json
from pathlib import Path

import numpy as np

from .data import feature_frame, labels


def generate_images(model, training, testing, output):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from scipy.spatial import ConvexHull
    from sklearn.decomposition import PCA
    from sklearn.preprocessing import StandardScaler
    import plotly.graph_objects as go

    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    frame = feature_frame(testing, model.keywords)
    y = labels(testing)
    files = []

    def save(fig, name):
        fig.tight_layout()
        fig.savefig(output / name, dpi=160, bbox_inches="tight")
        plt.close(fig)
        files.append(name)

    def draw(ax, index, legend=False):
        vault = model.vaults[index]
        points = frame[vault.features].to_numpy()
        for category, color, name in ((0, "#2563eb", "Held-out legitimate"),
                                      (1, "#dc2626", "Held-out phishing")):
            subset = points[y == category]
            ax.scatter(subset[:, 0], subset[:, 1], s=10, alpha=.5, c=color, label=name)
        core = vault.points
        if vault.rank == 2:
            vertices = ConvexHull(core).vertices
            ax.fill(core[vertices, 0], core[vertices, 1], color="#16a34a", alpha=.15,
                    label="Fitted legitimate core hull")
            boundary = core[np.r_[vertices, vertices[0]]]
            ax.plot(boundary[:, 0], boundary[:, 1], color="#15803d", linewidth=1)
        elif vault.rank == 1:
            order = np.argsort((core - vault.center) @ vault.basis[:, 0])
            ax.plot(core[order, 0], core[order, 1], color="#15803d", label="Fitted core line")
        else:
            ax.scatter(core[:, 0], core[:, 1], marker="*", s=70, c="#15803d", label="Fitted core point")
        ax.set(title=f"Vault {index + 1}", xlabel=vault.features[0], ylabel=vault.features[1])
        ax.grid(alpha=.2)
        if legend:
            ax.legend(fontsize=7)

    for i in range(len(model.vaults)):
        fig, ax = plt.subplots(figsize=(7, 5))
        draw(ax, i, legend=True)
        save(fig, f"vault_{i + 1:02d}.png")

    cols = min(4, len(model.vaults))
    rows = (len(model.vaults) + cols - 1) // cols
    fig, axes = plt.subplots(rows, cols, figsize=(cols * 5, rows * 4), squeeze=False)
    for i, ax in enumerate(axes.flat):
        if i < len(model.vaults):
            draw(ax, i)
        else:
            ax.set_visible(False)
    save(fig, "all_vaults.png")

    # Rank on training phishing records, not on the held-out evaluation set.
    train_frame = feature_frame(training, model.keywords)
    train_y = labels(training)
    scores = [int((~v.contains(train_frame.loc[train_y == 1, v.features].to_numpy())).sum())
              for v in model.vaults]
    top = sorted(range(len(scores)), key=lambda i: (-scores[i], i))[:3]
    fig, axes = plt.subplots(1, len(top), figsize=(7 * len(top), 5), squeeze=False)
    for ax, i in zip(axes.flat, top):
        draw(ax, i, legend=True)
    fig.suptitle("Top vaults ranked by training phishing rejection; points show held-out data")
    save(fig, "top_vaults.png")

    fig, ax = plt.subplots(figsize=(10, max(4, len(scores) * .25)))
    ax.barh([f"Vault {i + 1}" for i in range(len(scores))], scores, color="#2563eb")
    ax.set(xlabel="Training phishing records outside this vault", title="Per-vault training rejection counts")
    save(fig, "vault_rejection_counts.png")

    # PCA is a visualization only; it does not replace the fitted vault classifier.
    scaler = StandardScaler().fit(train_frame[model.features])
    dimensions = min(3, len(model.features), len(training))
    pca = PCA(n_components=dimensions).fit(scaler.transform(train_frame[model.features]))
    projected = pca.transform(scaler.transform(frame[model.features]))
    fig, ax = plt.subplots(figsize=(8, 6))
    for category, color, name in ((0, "#2563eb", "Legitimate"), (1, "#dc2626", "Phishing")):
        points = projected[y == category]
        ax.scatter(points[:, 0], points[:, 1], s=15, alpha=.6, c=color, label=name)
    ax.set(xlabel="PC1", ylabel="PC2", title="Held-out data: PCA fitted on training features")
    ax.legend()
    save(fig, "pca_2d.png")

    if dimensions == 3:
        fig = plt.figure(figsize=(9, 7))
        ax = fig.add_subplot(111, projection="3d")
        interactive = go.Figure()
        for category, color, name in ((0, "#2563eb", "Legitimate"), (1, "#dc2626", "Phishing")):
            points = projected[y == category]
            ax.scatter(*points.T, s=15, alpha=.6, c=color, label=name)
            interactive.add_trace(go.Scatter3d(x=points[:, 0], y=points[:, 1], z=points[:, 2],
                                               mode="markers", name=name,
                                               marker={"size": 3, "color": color, "opacity": .6}))
        ax.set(xlabel="PC1", ylabel="PC2", zlabel="PC3", title="Held-out PCA visualization")
        ax.legend()
        save(fig, "pca_3d.png")
        interactive.update_layout(title="Held-out PCA visualization (not a classification boundary)",
                                  scene={"xaxis_title": "PC1", "yaxis_title": "PC2", "zaxis_title": "PC3"})
        interactive.write_html(output / "interactive_3d.html", include_plotlyjs=True)
        files.append("interactive_3d.html")
    (output / "manifest.json").write_text(json.dumps({
        "files": files, "vault_count": len(model.vaults),
        "pca_explained_variance_ratio": pca.explained_variance_ratio_.tolist(),
        "note": "Plots regenerated from this run; historical reference images are not overwritten."
    }, indent=2) + "\n", encoding="utf-8")
    return files
