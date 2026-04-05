from sqlalchemy import String, ForeignKey, Text, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import TimestampMixin, generate_uuid


class SiteReview(Base, TimestampMixin):
    __tablename__ = "site_reviews"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    site_id: Mapped[str] = mapped_column(String, ForeignKey("sites.id"), nullable=False, index=True)

    source: Mapped[str] = mapped_column(String, nullable=False)  # google | yandex | 2gis | tripadvisor
    rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    text: Mapped[str | None] = mapped_column(Text, nullable=True)
    author: Mapped[str | None] = mapped_column(String, nullable=True)
    review_date: Mapped[str | None] = mapped_column(String, nullable=True)

    site: Mapped["Site"] = relationship("Site", back_populates="reviews")
