from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db

app = FastAPI(title="Barbeiro ARTP API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/mentores", response_model=list[schemas.Mentor])
def listar_mentores(db: Session = Depends(get_db)):
    return db.query(models.Mentor).join(models.Usuario).filter(models.Usuario.ativo.is_(True)).all()
