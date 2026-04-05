from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import TimestampMixin, generate_uuid


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    propelauth_user_id: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String, nullable=False, index=True)
    plan: Mapped[str] = mapped_column(String, default="free", nullable=False)  # free, pro, agency, white_label
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    sites: Mapped[list["Site"]] = relationship("Site", back_populates="user")
