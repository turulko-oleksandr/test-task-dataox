from sqlalchemy import (
    Column,
    Integer,
    String,
    BigInteger,
    DateTime,
    Boolean,
    Text,
    Index,
    CheckConstraint,
)
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
import datetime
import uuid

from src.database.session import Base


class CarAd(Base):
    """Model for car advertisement from AutoRia."""

    __tablename__ = "car_ads"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Required fields
    url = Column(String(500), nullable=False, unique=True, index=True)
    title = Column(String(255), nullable=False)
    price_usd = Column(Integer, nullable=False)  # Price in USD

    # Car details
    odometer = Column(Integer, nullable=False)  # Converted from "95 тис." to 95000
    username = Column(String(100))
    phone_number = Column(BigInteger)  # Format: 38063xxxxxx
    image_url = Column(String(500))
    images_count = Column(Integer, default=0)
    car_number = Column(String(20))  # License plate
    car_vin = Column(String(17))  # VIN code (17 characters)

    # Metadata
    datetime_found = Column(DateTime, default=datetime.datetime.utcnow)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(
        DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )
    is_active = Column(Boolean, default=True, index=True)

    # Additional fields for better filtering
    brand = Column(String(50))
    model = Column(String(50))
    year = Column(Integer)
    location = Column(String(100))

    # Text search field for full-text search
    search_text = Column(Text)

    # Constraints
    __table_args__ = (
        # Ensure price is positive
        CheckConstraint("price_usd >= 0", name="check_price_positive"),
        # Ensure odometer is positive
        CheckConstraint("odometer >= 0", name="check_odometer_positive"),
        # Ensure images_count is positive
        CheckConstraint("images_count >= 0", name="check_images_count_positive"),
        # Index for common queries
        Index("idx_car_ads_price_odometer", "price_usd", "odometer"),
        Index("idx_car_ads_year_brand", "year", "brand"),
        Index("idx_car_ads_created_at", "created_at"),
        # Partial index for active ads
        Index("idx_car_ads_active", "is_active", "created_at"),
    )

    def __repr__(self):
        return f"<CarAd(id={self.id}, title='{self.title[:30]}...', price={self.price_usd} USD)>"

    def to_dict(self):
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "url": self.url,
            "title": self.title,
            "price_usd": self.price_usd,
            "odometer": self.odometer,
            "username": self.username,
            "phone_number": str(self.phone_number) if self.phone_number else None,
            "image_url": self.image_url,
            "images_count": self.images_count,
            "car_number": self.car_number,
            "car_vin": self.car_vin,
            "datetime_found": (
                self.datetime_found.isoformat() if self.datetime_found else None
            ),
            "brand": self.brand,
            "model": self.model,
            "year": self.year,
            "location": self.location,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ScrapingLog(Base):
    """Model for logging scraping sessions."""

    __tablename__ = "scraping_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True)
    start_time = Column(DateTime, default=datetime.datetime.utcnow)
    end_time = Column(DateTime)
    status = Column(String(20), default="running")  # running, completed, failed
    ads_scraped = Column(Integer, default=0)
    ads_duplicates = Column(Integer, default=0)
    errors_count = Column(Integer, default=0)
    duration_seconds = Column(Integer)

    def complete(
        self, ads_scraped: int = 0, ads_duplicates: int = 0, errors_count: int = 0
    ):
        """Mark scraping session as completed."""
        self.end_time = datetime.datetime.utcnow()
        self.status = "completed"
        self.ads_scraped = ads_scraped
        self.ads_duplicates = ads_duplicates
        self.errors_count = errors_count
        self.duration_seconds = (self.end_time - self.start_time).total_seconds()
