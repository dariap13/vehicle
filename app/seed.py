"""Seed danych przykładowych zgodnych z treścią zadania."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Owner, TransactionHistory, Vehicle, VehicleImage

SAMPLE_IMAGE_SOURCES: dict[int, dict[str, str]] = {
    1: {
        "filename": "vehicle_1.jpg",
        "remote_url": (
            "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a4/"
            "2019_Toyota_Corolla_Hybrid_1.8.jpg/640px-2019_Toyota_Corolla_Hybrid_1.8.jpg"
        ),
    },
    2: {
        "filename": "vehicle_2.jpg",
        "remote_url": (
            "https://upload.wikimedia.org/wikipedia/commons/thumb/0/02/"
            "BMW_G05_IMG_3520.jpg/640px-BMW_G05_IMG_3520.jpg"
        ),
    },
    3: {
        "filename": "vehicle_3.jpg",
        "remote_url": (
            "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e7/"
            "MAN_TGS_18.440_4X2_BLS.jpg/640px-MAN_TGS_18.440_4X2_BLS.jpg"
        ),
    },
    4: {
        "filename": "vehicle_4.jpg",
        "remote_url": (
            "https://upload.wikimedia.org/wikipedia/commons/thumb/8/87/"
            "2007_Honda_CBR600RR.jpg/640px-2007_Honda_CBR600RR.jpg"
        ),
    },
    5: {
        "filename": "vehicle_5.jpg",
        "remote_url": (
            "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f8/"
            "Skoda_Octavia_III_front_20130414.jpg/640px-Skoda_Octavia_III_front_20130414.jpg"
        ),
    },
}


def resolve_image_reference(vehicle_id: int) -> str:
    image = SAMPLE_IMAGE_SOURCES[vehicle_id]
    local_path = settings.images_dir / image["filename"]
    if local_path.exists():
        return str(Path("images") / image["filename"])
    return image["remote_url"]


def seed_database(session: Session) -> None:
    already_seeded = session.scalar(select(Vehicle.vehicle_id).limit(1))
    if already_seeded is not None:
        _refresh_image_references(session)
        return

    owners = [
        Owner(owner_id=1, first_name="Jan", last_name="Kowalski", city="Warszawa"),
        Owner(owner_id=2, first_name="Anna", last_name="Nowak", city="Krakow"),
        Owner(owner_id=3, first_name="Piotr", last_name="Zielinski", city="Gdansk"),
        Owner(owner_id=4, first_name="Maria", last_name="Wisniewska", city="Poznan"),
    ]

    vehicles = [
        Vehicle(
            vehicle_id=1,
            brand="Toyota",
            model="Corolla",
            year=2018,
            price=Decimal("45000.00"),
            availability="sold",
        ),
        Vehicle(
            vehicle_id=2,
            brand="BMW",
            model="X5",
            year=2020,
            price=Decimal("180000.00"),
            availability="sold",
        ),
        Vehicle(
            vehicle_id=3,
            brand="MAN",
            model="TGS",
            year=2017,
            price=Decimal("350000.00"),
            availability="sold",
        ),
        Vehicle(
            vehicle_id=4,
            brand="Honda",
            model="CBR600RR",
            year=2019,
            price=Decimal("38000.00"),
            availability="sold",
        ),
        Vehicle(
            vehicle_id=5,
            brand="Skoda",
            model="Octavia",
            year=2016,
            price=Decimal("32000.00"),
            availability="available",
        ),
    ]

    transactions = [
        TransactionHistory(
            transaction_id=1,
            vehicle_id=1,
            buyer_id=1,
            seller_id=None,
            transaction_date=date(2021, 5, 12),
            price=Decimal("45000.00"),
        ),
        TransactionHistory(
            transaction_id=2,
            vehicle_id=2,
            buyer_id=2,
            seller_id=None,
            transaction_date=date(2022, 1, 8),
            price=Decimal("180000.00"),
        ),
        TransactionHistory(
            transaction_id=3,
            vehicle_id=3,
            buyer_id=3,
            seller_id=None,
            transaction_date=date(2019, 9, 20),
            price=Decimal("350000.00"),
        ),
        TransactionHistory(
            transaction_id=4,
            vehicle_id=1,
            buyer_id=4,
            seller_id=1,
            transaction_date=date(2023, 2, 15),
            price=Decimal("40000.00"),
        ),
        TransactionHistory(
            transaction_id=5,
            vehicle_id=4,
            buyer_id=1,
            seller_id=None,
            transaction_date=date(2020, 7, 3),
            price=Decimal("38000.00"),
        ),
    ]

    images = [
        VehicleImage(image_id=1, vehicle_id=1, image_url=resolve_image_reference(1)),
        VehicleImage(image_id=2, vehicle_id=2, image_url=resolve_image_reference(2)),
        VehicleImage(image_id=3, vehicle_id=3, image_url=resolve_image_reference(3)),
        VehicleImage(image_id=4, vehicle_id=4, image_url=resolve_image_reference(4)),
        VehicleImage(image_id=5, vehicle_id=5, image_url=resolve_image_reference(5)),
    ]

    session.add_all(owners)
    session.add_all(vehicles)
    session.add_all(transactions)
    session.add_all(images)
    session.commit()


def _refresh_image_references(session: Session) -> None:
    existing_images = session.query(VehicleImage).all()
    updated = False
    for image in existing_images:
        resolved_reference = resolve_image_reference(image.vehicle_id)
        if image.image_url != resolved_reference:
            image.image_url = resolved_reference
            updated = True

    if updated:
        session.commit()
