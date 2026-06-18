from datetime import datetime, timezone

from sqlalchemy import Integer, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.base import Base


class TesteAptidao(Base):
    __tablename__ = "testes_aptidao"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    finalizado: Mapped[bool] = mapped_column(Boolean, default=False)
    pontuacao: Mapped[float] = mapped_column(Float, default=0)
    iniciado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    finalizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    usuario = relationship("User", back_populates="testes_aptidao")
    respostas = relationship("RespostaQuestao", back_populates="teste_aptidao", cascade="all, delete-orphan")
    questoes = relationship("TesteQuestao", back_populates="teste", cascade="all, delete-orphan")