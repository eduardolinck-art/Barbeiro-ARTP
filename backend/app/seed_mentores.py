"""Cadastra mentores iniciais. Rode com: python -m app.seed_mentores"""

from app.database import SessionLocal
from app.models import Mentor, Papel, Usuario

NOMES_MENTORES = [
    "Cacia Rosângela Portal",
    "Carine",
    "Carolina da Silva Silveira",
    "Caroline Bonora",
    "Caroline Silveira Dias",
    "Denise Hailliot",
    "Jane Biondo",
    "Karem Zapana",
    "Leonardo Bavaresco",
    "Rosana Agostini",
    "Vitor Hugo Magni D'Avila",
]


def seed():
    db = SessionLocal()
    try:
        criados = 0
        for nome in NOMES_MENTORES:
            ja_existe = db.query(Usuario).filter(Usuario.nome == nome, Usuario.papel == Papel.mentor).first()
            if ja_existe:
                continue
            usuario = Usuario(nome=nome, papel=Papel.mentor)
            db.add(usuario)
            db.flush()
            db.add(Mentor(id=usuario.id))
            criados += 1
        db.commit()
        print(f"{criados} mentor(es) cadastrado(s). {len(NOMES_MENTORES) - criados} já existiam.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
