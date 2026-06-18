from sqlalchemy import Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.base import Base

class QuestaoSalva(Base):
    __tablename__ = "questoes_salvas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    questao_id: Mapped[int] = mapped_column(ForeignKey("questoes.id"))

    usuario = relationship("User", back_populates="questoes_salvas")
    questao = relationship("Questao", back_populates="questoes_salvas")