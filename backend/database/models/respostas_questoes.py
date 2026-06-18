from datetime import datetime, timezone

from sqlalchemy import Integer, Boolean, ForeignKey, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.base import Base

class RespostaQuestao(Base):
    __tablename__ = "respostas_questoes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    questao_id: Mapped[int] = mapped_column(ForeignKey("questoes.id"))
    teste_aptidao_id: Mapped[int] = mapped_column(ForeignKey("testes_aptidao.id"), nullable=True)
    resposta_usuario: Mapped[str] = mapped_column(String(1), nullable=False)
    acertou: Mapped[bool] = mapped_column(Boolean)
    data_resposta: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    usuario = relationship("User", back_populates="respostas")
    questao = relationship("Questao", back_populates="respostas")
    teste_aptidao = relationship("TesteAptidao")