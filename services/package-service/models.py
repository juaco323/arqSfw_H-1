from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.sql import func

from database import Base


class Package(Base):
    __tablename__ = "packages"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    tracking_code = Column(String(64), nullable=False, unique=True, index=True)
    package_title = Column(String(200), nullable=True)
    city = Column(String(100), nullable=True)
    location = Column(String(200), nullable=True)
    current_status = Column(String(50), nullable=False, default="CREATED")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
