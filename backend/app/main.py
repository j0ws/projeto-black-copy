from fastapi import FastAPI, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import time

from app.database import engine, Base, get_db
from app.models import domain

# Inicializa as tabelas do SQLite (Para MVP fácil sem Alembic no dia 1)
domain.Base.metadata.create_all(bind=engine)

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine
from app.models import domain
from app.routers import scraper, miner

# Criação das tabelas para o MVP (SQLite)
domain.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Caçador de Criativos (Backend)",
    description="""
API do Orquestrador de Inteligência de Anúncios.
## Recursos (Tags)
* **📉 Kalodata & Intelligence:** Busca produtos febris e rastreia canais por lucro final.
* **⚙️ Prospector & Editor:** Enfilera processamento pesado Assíncrono para transcrição, LLM Ad Copying e Recorte de Vídeo via FFmpeg.
""",
    version="1.0.0"
)

# Adicionando CORS para o futuro Front-End/App web conseguir bater na API limpo
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(scraper.router)
app.include_router(miner.router)

# Rota raiz que redireciona imediatamente para a documentação do Swagger
@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")
