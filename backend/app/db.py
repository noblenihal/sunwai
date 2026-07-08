from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from .config import settings

engine = create_engine(settings.database_url, pool_size=5, max_overflow=2)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ping() -> bool:
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return True
