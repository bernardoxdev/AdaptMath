from sqlalchemy import Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.base import Base


class TesteQuestao(Base):
    __tablename__ = "teste_questoes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    teste_id: Mapped[int] = mapped_column(ForeignKey("testes_aptidao.id"), nullable=False)
    questao_id: Mapped[int] = mapped_column(ForeignKey("questoes.id"), nullable=False)
    ordem: Mapped[int] = mapped_column(Integer,default=0)

    teste = relationship("TesteAptidao", back_populates="questoes")
    questao = relationship("Questao", back_populates="testes")