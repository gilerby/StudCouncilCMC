from datetime import datetime

from sqlalchemy import String, func
from sqlalchemy.orm import Mapped, mapped_column

from models.db import Base


class VotingInfo(Base):
    __tablename__ = "voting_info"

    faculty: Mapped[str] = mapped_column()
    course: Mapped[str] = mapped_column()
    end_time: Mapped[datetime] = mapped_column()

    name: Mapped[str] = mapped_column(String(50), nullable=True)
    description: Mapped[str] = mapped_column(String(300), nullable=True)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    def __repr__(self) -> str:
        return (
            f"VotingInfo(id={self.id!r}, name={self.name!r}, faculty={self.faculty!r}, "
            f"course={self.course!r}, end_time={self.end_time!r})"
        )
