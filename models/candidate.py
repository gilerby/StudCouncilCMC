from datetime import datetime

from sqlalchemy import ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.db import Base


class Candidate(Base):
    __tablename__ = "candidate"

    voting_id: Mapped[int] = mapped_column(
        ForeignKey("voting_info.id", ondelete="CASCADE")
    )
    name: Mapped[str] = mapped_column(String(255))
    link: Mapped[str] = mapped_column(String(255))
    about: Mapped[str] = mapped_column(String(1023))
    course: Mapped[str] = mapped_column()

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    votes: Mapped[list["VoteForCandidate"]] = relationship(back_populates="candidate")

    def __repr__(self) -> str:
        return f"Candidate({self.id=!r}, {self.voting_id=!r}, {self.name=!r})"
