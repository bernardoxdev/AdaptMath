from sqlalchemy import Integer, String, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.base import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    nome: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    senha: Mapped[str] = mapped_column(String(255), nullable=False)

    nivel_medio: Mapped[float] = mapped_column(Float, default=1.0)

    respostas = relationship("RespostaQuestao", back_populates="usuario", cascade="all, delete-orphan")
    testes_aptidao = relationship("TesteAptidao", back_populates="usuario", cascade="all, delete-orphan")
    questoes_salvas = relationship("QuestaoSalva", back_populates="usuario", cascade="all, delete-orphan")
    questoes_reportadas = relationship("QuestaoReportada", back_populates="usuario", cascade="all, delete-orphan")
    conversas = relationship("Conversas", back_populates="usuario", cascade="all, delete-orphan")