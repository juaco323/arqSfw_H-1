from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from database import Base


class TrackingEvent(Base):
    __tablename__ = "tracking_events"

    id = Column(Integer, primary_key=True, index=True)
    tracking_code = Column(String(64), nullable=False, index=True)
    user_id = Column(Integer, nullable=True)
    status = Column(String(50), nullable=False)
    location = Column(String(200), nullable=True)
    event_note = Column(Text, nullable=True)
    recorded_at = Column(DateTime(timezone=True), server_default=func.now())
