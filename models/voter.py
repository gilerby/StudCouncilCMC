from datetime import datetime

from sqlalchemy import ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from models.db import Base


class Voter(Base):
    __tablename__ = "voter"

    voting_id: Mapped[int] = mapped_column(
        ForeignKey("voting_info.id", ondelete="CASCADE")
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"))
    student_id: Mapped[int] = mapped_column(ForeignKey("student.id", ondelete="CASCADE"))
    voter_uid: Mapped[str] = mapped_column(unique=True)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    __table_args__ = (UniqueConstraint("voting_id", "student_id"),)

    def __repr__(self) -> str:
        return f"Voter({self.id=!r}, {self.student_id=!r}, {self.voter_uid=!r})"
