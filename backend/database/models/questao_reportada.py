from datetime import datetime, timezone

from sqlalchemy import Integer, ForeignKey, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.database.base import Base


class QuestaoReportada(Base):
    __tablename__ = "questoes_reportadas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    questao_id: Mapped[int] = mapped_column(ForeignKey("questoes.id"))
    usuario_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    tipo: Mapped[str] = mapped_column(Text)
    descricao: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    questao = relationship("Questao", back_populates="questoes_reportadas")
    usuario = relationship("User", back_populates="questoes_reportadas")