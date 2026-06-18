from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.core.config import DATABASE_URL

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

def get_db():
    if SessionLocal is None:
        raise RuntimeError("❌ Banco de dados não inicializado")

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()