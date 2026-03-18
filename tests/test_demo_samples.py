import json

from app.classifier.vehicle_classifier import get_demo_sample_override
from app.config import settings


def test_demo_sample_override_for_placeholder_image(tmp_path):
    images_dir = tmp_path / "images"
    images_dir.mkdir()
    sample_path = images_dir / "vehicle_4.jpg"
    sample_path.write_bytes(b"placeholder")
    manifest_path = images_dir / ".placeholder_manifest.json"
    manifest_path.write_text(json.dumps({"vehicle_4.jpg": 4}), encoding="utf-8")

    original_images_dir = settings.images_dir
    settings.images_dir = images_dir
    try:
        result = get_demo_sample_override(sample_path)
    finally:
        settings.images_dir = original_images_dir

    assert result is not None
    assert result.vehicle_type == "motocykl"
    assert result.is_vehicle is True
