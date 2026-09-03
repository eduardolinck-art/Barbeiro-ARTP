from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time


@dataclass
class Perfil:
    id: str
    nome: str
    celular: str
    email: str
    criado_em: datetime | None = None

    @classmethod
    def from_row(cls, row: dict) -> "Perfil":
        return cls(
            id=row["id"],
            nome=row["nome"],
            celular=row["celular"],
            email=row["email"],
            criado_em=row.get("criado_em"),
        )


@dataclass
class Mentor:
    id: str
    nome: str
    google_calendar_id: str | None = None
    google_refresh_token: str | None = None
    google_access_token: str | None = None
    token_expiry: datetime | None = None

    @classmethod
    def from_row(cls, row: dict) -> "Mentor":
        return cls(
            id=row["id"],
            nome=row["nome"],
            google_calendar_id=row.get("google_calendar_id"),
            google_refresh_token=row.get("google_refresh_token"),
            google_access_token=row.get("google_access_token"),
            token_expiry=row.get("token_expiry"),
        )


@dataclass
class Curso:
    id: str
    nome: str

    @classmethod
    def from_row(cls, row: dict) -> "Curso":
        return cls(id=row["id"], nome=row["nome"])


@dataclass
class Agendamento:
    id: str
    mentorado_id: str
    mentor_id: str
    curso_id: str
    data: date
    hora: time
    status: str
    protocolo: str
    google_event_id: str | None = None
    criado_em: datetime | None = None
    mentor_nome: str | None = None
    curso_nome: str | None = None

    @classmethod
    def from_row(cls, row: dict) -> "Agendamento":
        return cls(
            id=row["id"],
            mentorado_id=row["mentorado_id"],
            mentor_id=row["mentor_id"],
            curso_id=row["curso_id"],
            data=row["data"],
            hora=row["hora"],
            status=row["status"],
            protocolo=row["protocolo"],
            google_event_id=row.get("google_event_id"),
            criado_em=row.get("criado_em"),
            mentor_nome=(row.get("mentores") or {}).get("nome") if row.get("mentores") else None,
            curso_nome=(row.get("cursos") or {}).get("nome") if row.get("cursos") else None,
        )


@dataclass
class Avaliacao:
    id: str
    agendamento_id: str
    nota: int
    comentario: str | None = None
    criado_em: datetime | None = None

    @classmethod
    def from_row(cls, row: dict) -> "Avaliacao":
        return cls(
            id=row["id"],
            agendamento_id=row["agendamento_id"],
            nota=row["nota"],
            comentario=row.get("comentario"),
            criado_em=row.get("criado_em"),
        )
