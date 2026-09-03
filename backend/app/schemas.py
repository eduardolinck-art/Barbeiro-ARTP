from datetime import datetime

from pydantic import BaseModel

from app.models import Papel


class UsuarioBase(BaseModel):
    nome: str
    email: str | None = None
    papel: Papel


class Usuario(UsuarioBase):
    id: int
    ativo: bool
    criado_em: datetime

    class Config:
        from_attributes = True


class MentorBase(BaseModel):
    disciplinas: str | None = None
    bio: str | None = None


class Mentor(MentorBase):
    id: int
    usuario: Usuario

    class Config:
        from_attributes = True
