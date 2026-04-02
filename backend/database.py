"""
Conexión a base de datos — archivo separado solo por apariencia;
la app sigue acoplada al Session directamente en main.py.
"""
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USER = os.getenv("DB_USER", "tracker")
DB_PASSWORD = os.getenv("DB_PASSWORD", "tracker_secret")
DB_NAME = os.getenv("DB_NAME", "package_tracking")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_engine():
    return engine
