from pathlib import Path

FEATURES = Path(__file__).resolve().parents[1] / "src/intent_labeler/features"


def test_every_feature_has_a_readme():
    missing = [d.name for d in FEATURES.iterdir()
               if d.is_dir() and (d / "__init__.py").exists() and not (d / "README.md").is_file()]
    assert not missing, f"features without README.md: {missing}"
