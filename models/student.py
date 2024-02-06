from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import String, func
from sqlalchemy.orm import Mapped, Session, mapped_column

from models.db import Base


class Student(Base):
    __tablename__ = "student"

    name: Mapped[str] = mapped_column(String(255))
    student_id: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    faculty: Mapped[str] = mapped_column(String(255))
    course: Mapped[str] = mapped_column(String(30))
    group: Mapped[str] = mapped_column(String(30))

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    def __repr__(self) -> str:
        return f"Student({self.id=!r}, {self.created_at=!r}, {self.student_id=!r})"
