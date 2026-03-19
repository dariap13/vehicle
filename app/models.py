"""Modele ORM dla domeny pojazdów."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Vehicle(Base):
    __tablename__ = "vehicles"

    vehicle_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    brand: Mapped[str] = mapped_column(String(100), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    availability: Mapped[str] = mapped_column(String(32), nullable=False, default="available")

    transactions: Mapped[list["TransactionHistory"]] = relationship(
        back_populates="vehicle",
        cascade="all, delete-orphan",
    )
    images: Mapped[list["VehicleImage"]] = relationship(
        back_populates="vehicle",
        cascade="all, delete-orphan",
    )


class Owner(Base):
    __tablename__ = "owners"

    owner_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)

    purchases: Mapped[list["TransactionHistory"]] = relationship(
        back_populates="buyer",
        foreign_keys="TransactionHistory.buyer_id",
    )
    sales: Mapped[list["TransactionHistory"]] = relationship(
        back_populates="seller",
        foreign_keys="TransactionHistory.seller_id",
    )


class TransactionHistory(Base):
    __tablename__ = "transaction_history"

    transaction_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicles.vehicle_id"), nullable=False)
    buyer_id: Mapped[int] = mapped_column(ForeignKey("owners.owner_id"), nullable=False)
    seller_id: Mapped[int | None] = mapped_column(ForeignKey("owners.owner_id"), nullable=True)
    transaction_date: Mapped[date] = mapped_column(Date, nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    vehicle: Mapped[Vehicle] = relationship(back_populates="transactions")
    buyer: Mapped[Owner] = relationship(back_populates="purchases", foreign_keys=[buyer_id])
    seller: Mapped[Owner | None] = relationship(back_populates="sales", foreign_keys=[seller_id])


class VehicleImage(Base):
    __tablename__ = "vehicle_images"

    image_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicles.vehicle_id"), nullable=False)
    image_url: Mapped[str] = mapped_column(String(1000), nullable=False)

    vehicle: Mapped[Vehicle] = relationship(back_populates="images")


class ClassificationCache(Base):
    __tablename__ = "classification_cache"

    cache_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    image_reference: Mapped[str] = mapped_column(String(1000), unique=True, nullable=False)
    vehicle_type: Mapped[str] = mapped_column(String(100), nullable=False)
    imagenet_class: Mapped[str] = mapped_column(String(200), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    is_vehicle: Mapped[bool] = mapped_column(Boolean, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
