from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Any
from app.services.apify_service import scrape_tiktok_profile

router = APIRouter(
    prefix="/api/v1/scraper",
    tags=["🕷️ Scraper (Apify)"]
)

class TikTokProfileScrapeRequest(BaseModel):
    profile_url: str = Field(..., example="https://www.tiktok.com/@joaosaude", description="URL do perfil alvo no TikTok")
    max_videos: int = Field(5, example=5, description="Quantidade máxima de vídeos para recuperar")

class TikTokProfileScrapeResponse(BaseModel):
    message: str = Field(..., example="Scraping executado com sucesso.")
    count: int = Field(..., example=1)
    data: List[Any]

@router.post("/tiktok/profile", response_model=TikTokProfileScrapeResponse, summary="Faz raspagem de dados de um perfil do TikTok via Apify")
def scrape_profile(req: TikTokProfileScrapeRequest):
    """
    **Ferramenta de Coleta Direta (TikTok):**
    Permite raspar dados brutos de perfis para alimentar o banco de dados.
    """
    print(f"Request: scraping {req.profile_url}")
    
    try:
        results = scrape_tiktok_profile(
            profile_url=req.profile_url, 
            max_videos=req.max_videos
        )
        
        return {
            "message": "Dados raspidos via API Oficial do Apify.",
            "count": len(results),
            "data": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno no Scraper: {str(e)}")
