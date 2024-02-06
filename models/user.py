from datetime import datetime

from sqlalchemy import ForeignKey, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.db import Base


class User(Base):
    __tablename__ = "user"

    student_id: Mapped[int] = mapped_column(
        ForeignKey("student.id"), nullable=True, server_default=text("NULL")
    )
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    tg_users: Mapped[list["TGUser"]] = relationship(back_populates="user")
    vk_users: Mapped[list["VKUser"]] = relationship(back_populates="user")

    def __repr__(self) -> str:
        return f"User({self.id=!r}, {self.created_at=!r}, {self.student_id=!r})"
