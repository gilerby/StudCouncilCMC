from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.db import Base


class VKUser(Base):
    __tablename__ = "vk_user"

    vk_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=False
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"))

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="vk_users")

    def __repr__(self) -> str:
        return f"VKUser(vk_id={self.vk_id!r}, user_id={self.user_id!r})"
