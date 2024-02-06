from datetime import datetime

from sqlalchemy import BigInteger, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.db import Base


class TGUser(Base):
    __tablename__ = "tg_user"

    tg_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=False
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"))

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="tg_users")

    def __repr__(self) -> str:
        return f"TGUser(user_id={self.user_id!r}, tg_id={self.tg_id!r})"
