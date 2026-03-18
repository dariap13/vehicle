"""Pobierz przykładowe zdjęcia pojazdów do katalogu images/."""

from __future__ import annotations

import json
import logging
from pathlib import Path

import requests
from PIL import Image, ImageDraw

from app.config import settings
from app.seed import SAMPLE_IMAGE_SOURCES

logger = logging.getLogger(__name__)
DEFAULT_HEADERS = {"User-Agent": "VehicleAIAgentRecruitmentTask/1.0"}
PLACEHOLDER_MANIFEST_FILENAME = ".placeholder_manifest.json"


def download_sample_images() -> list[Path]:
    settings.reload()
    settings.images_dir.mkdir(parents=True, exist_ok=True)

    downloaded: list[Path] = []
    placeholder_manifest: dict[str, int] = {}
    for vehicle_id, image in SAMPLE_IMAGE_SOURCES.items():
        target_path = settings.images_dir / image["filename"]
        if target_path.exists():
            downloaded.append(target_path)
            continue

        try:
            response = requests.get(image["remote_url"], timeout=30, headers=DEFAULT_HEADERS)
            response.raise_for_status()
            target_path.write_bytes(response.content)
            downloaded.append(target_path)
            logger.info("Pobrano obraz dla vehicle_id=%s do %s", vehicle_id, target_path)
        except Exception as exc:
            logger.warning("Nie udało się pobrać %s: %s", image["remote_url"], exc)
            _create_placeholder_image(vehicle_id, target_path)
            downloaded.append(target_path)
            placeholder_manifest[target_path.name] = vehicle_id
            logger.info(
                "Utworzono lokalny placeholder dla vehicle_id=%s w %s",
                vehicle_id,
                target_path,
            )

    _write_placeholder_manifest(placeholder_manifest)
    return downloaded


def _write_placeholder_manifest(placeholder_manifest: dict[str, int]) -> None:
    manifest_path = settings.images_dir / PLACEHOLDER_MANIFEST_FILENAME
    manifest_path.write_text(
        json.dumps(placeholder_manifest, indent=2, sort_keys=True),
        encoding="utf-8",
    )

def _create_placeholder_image(vehicle_id: int, target_path: Path) -> None:
    image = Image.new("RGB", (960, 540), color=(246, 248, 252))
    draw = ImageDraw.Draw(image)

    draw.rectangle((0, 380, 960, 540), fill=(228, 232, 239))
    draw.rectangle((0, 360, 960, 390), fill=(180, 185, 193))

    if vehicle_id in {1, 2, 5}:
        body_color = {
            1: (32, 123, 219),
            2: (47, 54, 64),
            5: (42, 157, 143),
        }[vehicle_id]
        draw.rounded_rectangle((180, 250, 780, 360), radius=30, fill=body_color)
        draw.polygon([(300, 250), (430, 180), (620, 180), (710, 250)], fill=body_color)
        draw.rectangle((360, 195, 470, 245), fill=(194, 224, 255))
        draw.rectangle((490, 195, 610, 245), fill=(194, 224, 255))
        draw.ellipse((250, 320, 360, 430), fill=(35, 35, 35))
        draw.ellipse((600, 320, 710, 430), fill=(35, 35, 35))
    elif vehicle_id == 3:
        draw.rectangle((120, 220, 600, 360), fill=(214, 86, 42))
        draw.rectangle((600, 250, 780, 360), fill=(214, 86, 42))
        draw.rectangle((620, 270, 730, 330), fill=(194, 224, 255))
        draw.ellipse((180, 320, 290, 430), fill=(35, 35, 35))
        draw.ellipse((430, 320, 540, 430), fill=(35, 35, 35))
        draw.ellipse((650, 320, 760, 430), fill=(35, 35, 35))
    elif vehicle_id == 4:
        draw.polygon([(250, 320), (400, 230), (550, 220), (720, 320)], fill=(200, 32, 54))
        draw.ellipse((320, 320, 430, 430), fill=(35, 35, 35))
        draw.ellipse((610, 320, 720, 430), fill=(35, 35, 35))
        draw.rectangle((500, 180, 530, 260), fill=(35, 35, 35))
    else:
        draw.rectangle((220, 240, 740, 360), fill=(95, 99, 104))
        draw.ellipse((260, 320, 370, 430), fill=(35, 35, 35))
        draw.ellipse((590, 320, 700, 430), fill=(35, 35, 35))

    draw.text((40, 40), f"vehicle_id={vehicle_id}", fill=(70, 76, 85))
    image.save(target_path, format="JPEG", quality=92)


if __name__ == "__main__":
    files = download_sample_images()
    if files:
        print(f"Pobrano lub znaleziono {len(files)} plikow w {settings.images_dir}")
    else:
        print("Nie pobrano zadnych plikow. Aplikacja nadal moze korzystac z URL-i zdalnych.")
