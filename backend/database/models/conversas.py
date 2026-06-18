from datetime import datetime, timezone

from sqlalchemy import Integer, ForeignKey, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.base import Base

class Conversas(Base):
    __tablename__ = "conversas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    titulo: Mapped[str] = mapped_column(Text, nullable=False, default='Nova Conversa')
    data: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    usuario = relationship("User", back_populates="conversas")
    mensagens = relationship("Mensagens", back_populates="conversa", cascade="all, delete-orphan")