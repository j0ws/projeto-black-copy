from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Optional
import os

from app.services.miner_service import search_youtube_videos, get_youtube_highlights, download_video_clip

router = APIRouter(
    prefix="/api/v1/miner",
    tags=["⛏️ Miner (Clips Virais)"]
)

# ======= SCHEMAS =======
class MinerSearchRequest(BaseModel):
    query: str = Field(..., example="suco verde emagrecer", description="Termo de busca para encontrar vídeos")
    platform: str = Field("youtube", example="youtube", description="Plataforma alvo: 'youtube' ou 'tiktok'")
    max_results: int = Field(10, description="Quantidade máxima de vídeos para retornar")

class ClipRequest(BaseModel):
    video_url: str = Field(..., example="https://www.youtube.com/watch?v=12345")
    start_time: float = Field(..., example=45.5, description="Segundo exato de início do clipe")
    end_time: float = Field(..., example=60.0, description="Segundo exato de fim do clipe (Max 30s de diferença do start)")

class DownloadClipsRequest(BaseModel):
    clips: List[ClipRequest]

# ======= ENDPOINTS =======

@router.post("/search", summary="Busca vídeos baseados na palavra-chave e plataforma")
def miner_search(req: MinerSearchRequest):
    """
    **Módulo 1: Miner - Passo 1**
    Faz a busca de vídeos virais na plataforma selecionada.
    """
    if req.platform.lower() == "youtube":
        return {"data": search_youtube_videos(query=req.query, max_results=req.max_results)}
    elif req.platform.lower() == "tiktok":
        # Futuro: Integrar com a busca do Apify Service se necessário
        raise HTTPException(status_code=501, detail="Pesquisa no TikTok através do Miner será ativada em breve.")
    else:
        raise HTTPException(status_code=400, detail="Plataforma não suportada. Use 'youtube' ou 'tiktok'.")


@router.get("/highlights", summary="Busca a minutagem exata da palavra-chave no vídeo")
def miner_get_highlights(video_url: str = Query(...), query_word: str = Query(...)):
    """
    **Módulo 1: Miner - Passo 2**
    Puxa a transcrição do vídeo (atualmente apenas YouTube) e encontra exatamente onde a pessoa falou
    a palavra pesquisada. Útil para renderizar a UI de preview (0.5s a 10s).
    """
    if "youtube.com" in video_url or "youtu.be" in video_url:
        return get_youtube_highlights(video_url, query_word)
    else:
        raise HTTPException(status_code=501, detail="Transcrição automática atualmente suportada apenas para YouTube.")


@router.post("/download-clips", summary="Recorta e empacota os fragmentos de vídeo selecionados")
def miner_download_clips(req: DownloadClipsRequest):
    """
    **Módulo 1: Miner - Passo 3**
    Envia a lista de clipes selecionados (com ajustos de slider).
    O backend recorta usando o `yt-dlp` e baixa EXATAMENTE aquele pedaço (Max 30seg por clipe).
    """
    downloaded_files = []
    
    for idx, clip in enumerate(req.clips):
        # Validação de Segurança
        if (clip.end_time - clip.start_time) > 30:
            raise HTTPException(status_code=400, detail=f"O clipe {idx} excede o limite máximo de 30 segundos.")
            
        output_name = f"clip_{idx}_miner"
        try:
            path = download_video_clip(clip.video_url, clip.start_time, clip.end_time, output_name)
            downloaded_files.append(path)
        except Exception as e:
            print(f"Erro ao empacotar clipe {idx}: {e}")
            
    if not downloaded_files:
        raise HTTPException(status_code=500, detail="Nenhum clipe pôde ser gerado.")
        
    return {
        "message": f"{len(downloaded_files)} clipes gerados com sucesso na pasta 'tmp_downloads'.",
        "files": downloaded_files
    }
