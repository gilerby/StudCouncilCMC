from datetime import datetime

from sqlalchemy import ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.db import Base


class VoteForCandidate(Base):
    __tablename__ = "vote_for_candidate"

    voting_id: Mapped[int] = mapped_column(
        ForeignKey("voting_info.id", ondelete="CASCADE")
    )

    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"))
    student_id: Mapped[str] = mapped_column(
        ForeignKey("student.id", ondelete="CASCADE")
    )
    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidate.id"))

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    candidate: Mapped["Candidate"] = relationship(back_populates="votes")

    def __repr__(self) -> str:
        return f"VoteForCandidate(id={self.id!r}, created_at={self.created_at!r})"
