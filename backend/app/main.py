from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine
from app.models import domain
from app.routers import miner

# Create tables for MVP (SQLite)
domain.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="BlackCopy AI - Miner Backend",
    description="""
API for the Ad Intelligence Orchestrator.
## Modules
* **⛏️ Miner:** Searches YouTube/TikTok for viral clips, extracts transcript highlights, and slices 20s stream chunks using FFmpeg.
""",
    version="1.0.0"
)

# Add CORS so the Frontend/Web App can hit the API locally
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(miner.router)

# Root route redirects immediately to Swagger documentation
@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")
