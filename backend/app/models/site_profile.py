from sqlalchemy import String, ForeignKey, Text, Float, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import TimestampMixin, generate_uuid


class SiteProfile(Base, TimestampMixin):
    __tablename__ = "site_profiles"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    site_id: Mapped[str] = mapped_column(String, ForeignKey("sites.id"), nullable=False, unique=True, index=True)

    # Business Info
    business_name: Mapped[str | None] = mapped_column(String, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    short_description: Mapped[str | None] = mapped_column(String(300), nullable=True)

    # Business Type (schema.org type)
    business_type: Mapped[str | None] = mapped_column(String, nullable=True)  # LocalBusiness, Store, etc.
    business_category: Mapped[str | None] = mapped_column(String, nullable=True)  # restaurant, salon, clinic

    # Location
    address: Mapped[str | None] = mapped_column(String, nullable=True)
    city: Mapped[str | None] = mapped_column(String, nullable=True)
    country: Mapped[str | None] = mapped_column(String, default="RU", nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Contact
    phone: Mapped[str | None] = mapped_column(String, nullable=True)
    email: Mapped[str | None] = mapped_column(String, nullable=True)
    website: Mapped[str | None] = mapped_column(String, nullable=True)
    hours: Mapped[str | None] = mapped_column(String, nullable=True)  # "Mon-Fri 9:00-18:00"

    # Social
    instagram: Mapped[str | None] = mapped_column(String, nullable=True)
    vk: Mapped[str | None] = mapped_column(String, nullable=True)
    telegram_channel: Mapped[str | None] = mapped_column(String, nullable=True)

    # Products & Services (JSON array)
    # [{"name": "...", "description": "...", "price": "...", "category": "..."}]
    products_services: Mapped[list | None] = mapped_column(JSON, nullable=True)

    # FAQ (JSON array)
    # [{"question": "...", "answer": "..."}]
    faq: Mapped[list | None] = mapped_column(JSON, nullable=True)

    # Target keywords for AI monitoring
    # ["барбершоп чертаново", "лучший барбершоп москва"]
    target_queries: Mapped[list | None] = mapped_column(JSON, nullable=True)

    # Unique features/amenities ["Парковка", "Wi-Fi", "Детская комната"]
    unique_features: Mapped[list | None] = mapped_column(JSON, nullable=True)

    # Ratings
    google_rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    google_review_count: Mapped[int | None] = mapped_column(nullable=True)

    # Raw crawl data (for re-processing)
    raw_crawl_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    site: Mapped["Site"] = relationship("Site", back_populates="profile")
