from sqlalchemy import String, ForeignKey, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import TimestampMixin, generate_uuid


class SiteFile(Base, TimestampMixin):
    __tablename__ = "site_files"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    site_id: Mapped[str] = mapped_column(String, ForeignKey("sites.id"), nullable=False, index=True)

    # file_type: llms_txt | schema_json | faq_html | robots_patch | export_zip
    file_type: Mapped[str] = mapped_column(String, nullable=False)

    # Content stored inline for small files, R2 key for large
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    r2_key: Mapped[str | None] = mapped_column(String, nullable=True)
    public_url: Mapped[str | None] = mapped_column(String, nullable=True)

    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    site: Mapped["Site"] = relationship("Site", back_populates="files")
