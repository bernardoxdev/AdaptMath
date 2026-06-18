from sqlalchemy import Integer, String, Text, Float, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.base import Base

class Questao(Base):
    __tablename__ = "questoes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    titulo: Mapped[str] = mapped_column(Text, nullable=False)
    contexto: Mapped[str] = mapped_column(Text, nullable=True)
    texto_completo: Mapped[str] = mapped_column(Text, nullable=False)
    imagem_url: Mapped[str] = mapped_column(Text, nullable=True)
    alternativa_a: Mapped[str] = mapped_column(Text, nullable=True)
    alternativa_b: Mapped[str] = mapped_column(Text, nullable=True)
    alternativa_c: Mapped[str] = mapped_column(Text, nullable=True)
    alternativa_d: Mapped[str] = mapped_column(Text, nullable=True)
    alternativa_e: Mapped[str] = mapped_column(Text, nullable=True)
    alternativa_a_imagem: Mapped[str] = mapped_column(Text, nullable=True)
    alternativa_b_imagem: Mapped[str] = mapped_column(Text, nullable=True)
    alternativa_c_imagem: Mapped[str] = mapped_column(Text, nullable=True)
    alternativa_d_imagem: Mapped[str] = mapped_column(Text, nullable=True)
    alternativa_e_imagem: Mapped[str] = mapped_column(Text, nullable=True)
    resposta_correta: Mapped[str] = mapped_column(String(1), nullable=False)
    materia: Mapped[str] = mapped_column(String(100), nullable=False)
    assunto: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    habilidade_enem: Mapped[str] = mapped_column(String(50), nullable=True, index=True)
    dificuldade: Mapped[float] = mapped_column(Float, default=1.0, index=True)
    embedding: Mapped[str] = mapped_column(Text, nullable=True)
    origem: Mapped[str] = mapped_column(String(100), default="ENEM")
    ativa: Mapped[bool] = mapped_column(Boolean, default=True)

    respostas = relationship("RespostaQuestao", back_populates="questao")
    questoes_salvas = relationship("QuestaoSalva", back_populates="questao", cascade="all, delete-orphan")
    estatisticas = relationship("EstatisticaQuestao", back_populates="questao", uselist=False, cascade="all, delete-orphan")
    testes = relationship("TesteQuestao", back_populates="questao", cascade="all, delete-orphan")
    questoes_reportadas = relationship("QuestaoReportada", back_populates="questao", cascade="all, delete-orphan")