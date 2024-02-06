from datetime import datetime

from sqlalchemy import ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from models.db import Base


class VoteAgainstAll(Base):
    __tablename__ = "vote_against_all"

    voting_id: Mapped[int] = mapped_column(
        ForeignKey("voting_info.id", ondelete="CASCADE")
    )

    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"))
    student_id: Mapped[str] = mapped_column(ForeignKey("student.id", ondelete="CASCADE"), unique=True)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    def __repr__(self) -> str:
        return f"VoteAgainstAll(id={self.id!r}, created_at={self.created_at!r})"
