import json

from examples.make_demo import make_records
from run_all import run


def test_pipeline_outputs_and_holdout(tmp_path):
    data = tmp_path / "records.json"
    data.write_text(json.dumps(make_records()), encoding="utf-8")
    output = tmp_path / "results"
    report = run(data, output, all_images=True)
    assert report["training_records"] == 160
    assert report["held_out"]["records"] == 40
    assert len(json.loads((output / "predictions.json").read_text())) == 200
    assert len(json.loads((output / "held_out_predictions.json").read_text())) == 40
    assert (output / "confusion_matrix.png").read_bytes().startswith(b"\x89PNG")
    assert len((output / "vault_mapping.csv").read_text().splitlines()) == report["vaults"] + 1
    manifest = json.loads((output / "images/manifest.json").read_text())
    assert manifest["vault_count"] == report["vaults"]
    for filename in manifest["files"]:
        artifact = output / "images" / filename
        assert artifact.stat().st_size > 100
        if artifact.suffix == ".png":
            assert artifact.read_bytes().startswith(b"\x89PNG")
