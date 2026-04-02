"""
Modelos incompletos / inconsistentes con el resto del sistema.
Parte de la tabla "tracking_data" está definida aquí y parte se asume en SQL crudo en main.
"""
from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func

from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False)


class TrackingData(Base):
    """
    Tabla monolítica: mezcla identidad de usuario, paquete, estado y evento.
    Sin FKs reales a User (solo columna user_id numérica sin relación ORM).
    """
    __tablename__ = "tracking_data"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True)  # debería ser FK — no lo es
    username_redundant = Column(String(100), nullable=True)
    user_email_copy = Column(String(255), nullable=True)
    tracking_code = Column(String(64), nullable=False, index=True)
    package_title = Column(String(200), nullable=True)
    status = Column(String(50), nullable=False)
    location = Column(String(200), nullable=True)
    city = Column(String(100), nullable=True)
    event_note = Column(Text, nullable=True)
    recorded_at = Column(DateTime(timezone=True), server_default=func.now())
