from sqlalchemy import String, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import TimestampMixin, generate_uuid


class Site(Base, TimestampMixin):
    __tablename__ = "sites"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    user_id: Mapped[str | None] = mapped_column(String, ForeignKey("users.id"), nullable=True, index=True)
    url: Mapped[str] = mapped_column(String, nullable=False)
    domain: Mapped[str] = mapped_column(String, nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)

    # Status: pending | crawling | processing | generating | done | error
    status: Mapped[str] = mapped_column(String, default="pending", nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped["User | None"] = relationship("User", back_populates="sites")
    profile: Mapped["SiteProfile | None"] = relationship("SiteProfile", back_populates="site", uselist=False)
    files: Mapped[list["SiteFile"]] = relationship("SiteFile", back_populates="site")
    reviews: Mapped[list["SiteReview"]] = relationship("SiteReview", back_populates="site")
    generation_jobs: Mapped[list["GenerationJob"]] = relationship("GenerationJob", back_populates="site")
    monitoring_jobs: Mapped[list["MonitoringJob"]] = relationship("MonitoringJob", back_populates="site")
