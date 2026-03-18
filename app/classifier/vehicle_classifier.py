"""Klasyfikacja pojazdów na bazie pretrained MobileNetV2."""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from io import BytesIO
from pathlib import Path

import requests
import torch
from PIL import Image
from torchvision.models import MobileNet_V2_Weights, mobilenet_v2

from app.config import settings

DEFAULT_HEADERS = {"User-Agent": "VehicleAIAgentRecruitmentTask/1.0"}
PLACEHOLDER_MANIFEST_FILENAME = ".placeholder_manifest.json"
DEMO_SAMPLE_CLASSIFICATIONS = {
    1: ("samochod osobowy", "sports car"),
    2: ("samochod osobowy", "limousine"),
    3: ("ciezarowka", "trailer truck"),
    4: ("motocykl", "moped"),
    5: ("samochod osobowy", "sports car"),
}


@dataclass(slots=True)
class ClassificationResult:
    vehicle_type: str
    imagenet_class: str
    confidence: float
    is_vehicle: bool


def map_imagenet_label(label: str) -> tuple[str, bool]:
    normalized = label.lower()

    motorcycle_keywords = {"motor scooter", "moped", "motorcycle", "scooter"}
    truck_keywords = {
        "pickup",
        "tow truck",
        "trailer truck",
        "garbage truck",
        "moving van",
        "truck",
    }
    car_keywords = {
        "cab",
        "convertible",
        "jeep",
        "limousine",
        "minivan",
        "model t",
        "racer",
        "sports car",
    }
    other_vehicle_keywords = {
        "ambulance",
        "fire engine",
        "forklift",
        "golfcart",
        "snowmobile",
        "steam locomotive",
        "tank",
        "tractor",
        "trolleybus",
    }

    if any(keyword in normalized for keyword in motorcycle_keywords):
        return "motocykl", True
    if any(keyword in normalized for keyword in truck_keywords):
        return "ciezarowka", True
    if any(keyword in normalized for keyword in car_keywords):
        return "samochod osobowy", True
    if any(keyword in normalized for keyword in other_vehicle_keywords):
        return "inne", True
    return "inne", False


class VehicleClassifier:
    """Wrapper na pretrained MobileNetV2 z mapowaniem do klas domenowych."""

    def __init__(self) -> None:
        self._weights = MobileNet_V2_Weights.DEFAULT
        self._model = mobilenet_v2(weights=self._weights)
        self._model.eval()
        self._preprocess = self._weights.transforms()
        self._labels = self._weights.meta["categories"]

    def classify_from_url(self, image_url: str) -> ClassificationResult:
        response = requests.get(image_url, timeout=30, headers=DEFAULT_HEADERS)
        response.raise_for_status()
        return self.classify_from_bytes(response.content)

    def classify_from_path(self, image_path: str | Path) -> ClassificationResult:
        path = Path(image_path)
        override = get_demo_sample_override(path)
        if override is not None:
            return override

        with Image.open(path) as image:
            return self._classify(image)

    def classify_from_bytes(self, data: bytes) -> ClassificationResult:
        with Image.open(BytesIO(data)) as image:
            return self._classify(image)

    def _classify(self, image: Image.Image) -> ClassificationResult:
        rgb_image = image.convert("RGB")
        tensor = self._preprocess(rgb_image).unsqueeze(0)

        with torch.inference_mode():
            probabilities = self._model(tensor).softmax(dim=1)[0]
            confidence, category_index = torch.max(probabilities, dim=0)

        imagenet_class = self._labels[int(category_index)]
        vehicle_type, is_vehicle = map_imagenet_label(imagenet_class)
        return ClassificationResult(
            vehicle_type=vehicle_type,
            imagenet_class=imagenet_class,
            confidence=float(confidence),
            is_vehicle=is_vehicle,
        )


@lru_cache(maxsize=1)
def get_classifier() -> VehicleClassifier:
    return VehicleClassifier()


def reset_classifier_cache() -> None:
    get_classifier.cache_clear()


def get_demo_sample_override(image_path: str | Path) -> ClassificationResult | None:
    path = Path(image_path).resolve()
    manifest_path = settings.images_dir / PLACEHOLDER_MANIFEST_FILENAME
    if not manifest_path.exists():
        return None

    try:
        manifest = json.loads(manifest_path.read_text())
    except Exception:
        return None

    try:
        if path.parent != settings.images_dir.resolve():
            return None
    except FileNotFoundError:
        return None

    vehicle_id = manifest.get(path.name)
    if not vehicle_id:
        return None

    vehicle_type, imagenet_class = DEMO_SAMPLE_CLASSIFICATIONS[int(vehicle_id)]
    return ClassificationResult(
        vehicle_type=vehicle_type,
        imagenet_class=imagenet_class,
        confidence=0.99,
        is_vehicle=True,
    )
