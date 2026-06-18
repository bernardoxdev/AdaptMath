from backend.database.base import Base
from backend.database.connection import engine

import backend.database.models

def init_db():
    Base.metadata.create_all(bind=engine)