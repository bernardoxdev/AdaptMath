from sqlalchemy import Integer, ForeignKey, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.base import Base

class EstatisticaQuestao(Base):
    __tablename__ = "estatisticas_questoes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    questao_id: Mapped[int] = mapped_column(ForeignKey("questoes.id"))
    total_respostas: Mapped[int] = mapped_column(Integer, default=0)
    total_acertos: Mapped[int] = mapped_column(Integer, default=0)
    taxa_acerto: Mapped[float] = mapped_column(Float, default=0)

    questao = relationship("Questao", back_populates="estatisticas")