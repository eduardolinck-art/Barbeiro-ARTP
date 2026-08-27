from pydantic import BaseModel


class ClienteBase(BaseModel):
    nome: str
    telefone: str | None = None


class ClienteCreate(ClienteBase):
    pass


class Cliente(ClienteBase):
    id: int

    class Config:
        from_attributes = True
