from datetime import datetime
from sqlalchemy import String, ForeignKey, Text, Boolean, Float, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import TimestampMixin, generate_uuid


class GenerationJob(Base, TimestampMixin):
    __tablename__ = "generation_jobs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    site_id: Mapped[str] = mapped_column(String, ForeignKey("sites.id"), nullable=False, index=True)
    celery_task_id: Mapped[str | None] = mapped_column(String, nullable=True)

    # pending | started | crawling | processing | generating | done | error
    status: Mapped[str] = mapped_column(String, default="pending", nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Progress tracking
    progress_step: Mapped[str | None] = mapped_column(String, nullable=True)  # "crawling", "analyzing", etc.
    progress_pct: Mapped[int] = mapped_column(default=0, nullable=False)

    site: Mapped["Site"] = relationship("Site", back_populates="generation_jobs")


class MonitoringJob(Base, TimestampMixin):
    __tablename__ = "monitoring_jobs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    site_id: Mapped[str] = mapped_column(String, ForeignKey("sites.id"), nullable=False, index=True)

    query: Mapped[str] = mapped_column(String, nullable=False)
    engine: Mapped[str] = mapped_column(String, nullable=False)  # google_ai | claude | perplexity
    status: Mapped[str] = mapped_column(String, default="pending", nullable=False)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    site: Mapped["Site"] = relationship("Site", back_populates="monitoring_jobs")
    results: Mapped[list["MonitoringResult"]] = relationship("MonitoringResult", back_populates="job")


class MonitoringResult(Base):
    __tablename__ = "monitoring_results"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    job_id: Mapped[str] = mapped_column(String, ForeignKey("monitoring_jobs.id"), nullable=False, index=True)
    site_id: Mapped[str] = mapped_column(String, ForeignKey("sites.id"), nullable=False, index=True)

    engine: Mapped[str] = mapped_column(String, nullable=False)
    query: Mapped[str] = mapped_column(String, nullable=False)

    mentioned: Mapped[bool] = mapped_column(Boolean, default=False)
    position: Mapped[int | None] = mapped_column(nullable=True)  # rank in AI response
    snippet: Mapped[str | None] = mapped_column(Text, nullable=True)  # context around mention

    # Per-product mentions
    # [{"product": "Американо", "mentioned": true, "context": "..."}]
    product_mentions: Mapped[list | None] = mapped_column(JSON, nullable=True)

    # Competitors mentioned in same response
    competitor_mentions: Mapped[list | None] = mapped_column(JSON, nullable=True)

    # Full AI response (truncated)
    full_response: Mapped[str | None] = mapped_column(Text, nullable=True)

    checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    job: Mapped["MonitoringJob"] = relationship("MonitoringJob", back_populates="results")
