from sqlalchemy import Integer, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.base import Base

class Mensagens(Base):
    __tablename__ = "Mensagens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    conversa_id: Mapped[int] = mapped_column(ForeignKey("conversas.id"))
    tipo: Mapped[str] = mapped_column(String, nullable=False, default='user')
    texto: Mapped[str] = mapped_column(Text, nullable=False)
    
    conversa = relationship("Conversas", back_populates="mensagens")