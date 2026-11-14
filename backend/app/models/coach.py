from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models._util import utcnow


class CoachAgent(Base):
    """A student's own Edify Coach (agents/edify-coach), on its own Maritime machine. ``state`` is the last picture
    the coach sent back (plan, revision packs), kept so the dashboard opens without waking the coach."""

    __tablename__ = "coach_agents"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    mode: Mapped[str] = mapped_column(String(10), default="maritime")        # maritime | local
    agent_id: Mapped[str | None] = mapped_column(String(80), nullable=True)  # Maritime's id for the machine
    status: Mapped[str] = mapped_column(String(16), default="starting")      # starting | ready | failed
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    state: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    synced_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)
