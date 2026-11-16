"""Generate synthetic feature records for smoke tests, NOT research validation."""
import json
import random
from pathlib import Path


def make_records():
    rng = random.Random(42)
    records = []
    for status in (1, -1):
        for i in range(100):
            entropy = rng.uniform(2, 4) if status == 1 else rng.uniform(6, 9)
            records.append({
                "main_url": f"https://example.test/{status}/{i}",
                "main_domain": "example.test", "status": status,
                "main_entropy": entropy, "combined_entropy": entropy + rng.uniform(-0.2, 0.2),
                "internal_pages": [{"entropy": rng.uniform(2, 4)} for _ in range(rng.randrange(2, 8))],
                "external_links": ["https://example.org"] * rng.randrange(1, 5),
                "keyword_scores": {"login": rng.random(), "account": rng.random()},
            })
    return records


if __name__ == "__main__":
    path = Path(__file__).with_name("demo_records.json")
    path.write_text(json.dumps(make_records(), indent=2), encoding="utf-8")
    print(f"Wrote {path} (synthetic data only)")
