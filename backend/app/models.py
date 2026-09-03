import enum

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    SmallInteger,
    String,
    Text,
    Time,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship

from app.database import Base


class Papel(str, enum.Enum):
    mentorado = "mentorado"
    mentor = "mentor"
    admin = "admin"


class StatusAgendamento(str, enum.Enum):
    confirmado = "confirmado"
    cancelado = "cancelado"
    concluido = "concluido"


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=True)
    google_id = Column(String, unique=True, index=True, nullable=True)
    papel = Column(Enum(Papel), nullable=False)
    ativo = Column(Boolean, nullable=False, default=True)
    criado_em = Column(DateTime(timezone=True), server_default=func.now())

    mentor = relationship("Mentor", back_populates="usuario", uselist=False)


class Mentor(Base):
    __tablename__ = "mentores"

    id = Column(Integer, ForeignKey("usuarios.id"), primary_key=True)
    disciplinas = Column(String, nullable=True)
    bio = Column(Text, nullable=True)
    google_refresh_token = Column(Text, nullable=True)

    usuario = relationship("Usuario", back_populates="mentor")
    disponibilidades = relationship("Disponibilidade", back_populates="mentor")


class Disponibilidade(Base):
    __tablename__ = "disponibilidades"

    id = Column(Integer, primary_key=True, index=True)
    mentor_id = Column(Integer, ForeignKey("mentores.id"), nullable=False)
    dia_semana = Column(SmallInteger, nullable=False)  # 0 = segunda ... 6 = domingo
    hora_inicio = Column(Time, nullable=False)
    hora_fim = Column(Time, nullable=False)

    mentor = relationship("Mentor", back_populates="disponibilidades")


class Agendamento(Base):
    __tablename__ = "agendamentos"

    id = Column(Integer, primary_key=True, index=True)
    mentor_id = Column(Integer, ForeignKey("mentores.id"), nullable=False)
    mentorado_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    inicio = Column(DateTime(timezone=True), nullable=False)
    fim = Column(DateTime(timezone=True), nullable=False)
    status = Column(Enum(StatusAgendamento), nullable=False, default=StatusAgendamento.confirmado)
    google_event_id = Column(String, nullable=True)
    criado_em = Column(DateTime(timezone=True), server_default=func.now())

    mentor = relationship("Mentor")
    mentorado = relationship("Usuario")
    avaliacao = relationship("Avaliacao", back_populates="agendamento", uselist=False)


class Avaliacao(Base):
    __tablename__ = "avaliacoes"
    __table_args__ = (UniqueConstraint("agendamento_id"),)

    id = Column(Integer, primary_key=True, index=True)
    agendamento_id = Column(Integer, ForeignKey("agendamentos.id"), nullable=False)
    nota = Column(SmallInteger, nullable=False)
    comentario = Column(Text, nullable=True)
    criado_em = Column(DateTime(timezone=True), server_default=func.now())

    agendamento = relationship("Agendamento", back_populates="avaliacao")
