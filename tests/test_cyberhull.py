import json

import pytest

from cyberhull import CyberHull
from cyberhull.cli import main
from cyberhull.data import feature_frame, load_records
from cyberhull.model import Vault
from examples.make_demo import make_records


@pytest.mark.parametrize("points,queries,expected", [
    ([[0, 0], [1, 0], [1, 1], [0, 1]], [[0.5, 0.5], [1, 1], [2, 0.5]], [True, True, False]),
    ([[0, 0], [1, 1], [2, 2]], [[0.5, 0.5], [1, 0], [3, 3]], [True, False, False]),
    ([[1, 1], [1, 1]], [[1, 1], [2, 2]], [True, False]),
])
def test_geometric_membership(points, queries, expected):
    assert Vault(["a", "b"], points).contains(queries).tolist() == expected


def test_repeatable_fit_and_model_roundtrip(tmp_path):
    records = make_records()
    first = CyberHull().fit(records)
    second = CyberHull().fit(records)
    a, b = tmp_path / "a.json", tmp_path / "b.json"
    first.save(a)
    second.save(b)
    assert a.read_bytes() == b.read_bytes()
    assert first.predict(records) == CyberHull.load(a).predict(records)
    assert all(p["prediction"] == "Phishing" for p in first.predict(records[100:]))


def test_training_vocabulary_is_frozen():
    model = CyberHull().fit(make_records())
    records = make_records()[:2]
    expected = model.predict(records)
    for record in records:
        record.pop("status")
        record["keyword_scores"]["unseen"] = 999
    assert model.predict(records) == expected
    assert "unseen" not in model.keywords


def test_features_match_notebook():
    row = {"main_url": "abc", "main_domain": "ab", "main_entropy": 2,
           "internal_pages": [{"entropy": 2}, {"entropy": 4}, {}],
           "external_links": ["x"], "keyword_scores": {"login": 0.5}}
    assert feature_frame([row], ["login", "other"]).iloc[0].tolist() == [2, 0, 3, 2, 3, 1, 3, .5, 0]


def test_lfs_pointer_error(tmp_path):
    path = tmp_path / "data.json"
    path.write_text("version https://git-lfs.github.com/spec/v1\noid sha256:123")
    with pytest.raises(ValueError, match="Git LFS pointer"):
        load_records(path)


def test_legacy_json_sequence(tmp_path):
    path = tmp_path / "data.json"
    path.write_text('{"status":1}, {"status":-1},')
    assert len(load_records(path)) == 2


@pytest.mark.parametrize("value", [float("nan"), float("inf"), "bad"])
def test_invalid_numeric_features(value):
    with pytest.raises(ValueError, match="record 0"):
        feature_frame([{"main_entropy": value}], [])


def test_invalid_training_and_unfitted_model():
    with pytest.raises(ValueError, match="status"):
        CyberHull().fit([{}])
    with pytest.raises(ValueError, match="at least four"):
        CyberHull().fit(make_records()[:100])
    with pytest.raises(ValueError, match="nonconstant"):
        CyberHull().fit([{"status": s} for s in [1, -1] * 10])
    with pytest.raises(ValueError, match="Fit or load"):
        CyberHull().predict([{}])


def test_cli_train_predict_evaluate(tmp_path, capsys):
    data, model, report = [tmp_path / name for name in ("data.json", "model.json", "report.json")]
    data.write_text(json.dumps(make_records()))
    main(["train", "--data", str(data), "--model", str(model), "--output", str(report)])
    metrics = json.loads(report.read_text())
    assert metrics["training_records"] == 160
    assert metrics["held_out"]["records"] == 40
    assert "false_positive_rate" in metrics["held_out"]
    main(["predict", "--data", str(data), "--model", str(model), "--output", str(report)])
    assert len(json.loads(report.read_text())) == 200
    main(["evaluate", "--data", str(data), "--model", str(model), "--output", str(report)])
    assert json.loads(report.read_text())["records"] == 200
