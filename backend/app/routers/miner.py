from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional

from app.services.miner_service import search_youtube_videos, get_youtube_highlights, download_video_clip, mock_tiktok_search

router = APIRouter(
    prefix="/api/v1/miner",
    tags=["⛏️ Miner (Viral Clips)"]
)

# ======= SCHEMAS =======
class MinerSearchRequest(BaseModel):
    query: str = Field(..., example="suco verde emagrecer", description="Search term or keyword")
    platform: str = Field("youtube", example="youtube", description="Target platform: 'youtube' or 'tiktok'")
    max_results: int = Field(10, description="Max amount of videos to return")
    filter_time: Optional[str] = Field(None, example="30d", description="Time filter: '24h' or '30d'")
    channel_name: Optional[str] = Field(None, example="growth_saude", description="Specific channel to search within")
    # sort_by could be implemented later on yt-dlp layer or post-processing

class ClipRequest(BaseModel):
    video_url: str = Field(..., example="https://www.youtube.com/watch?v=12345")
    start_time: float = Field(..., example=45.5, description="Exact start second of the clip")
    end_time: float = Field(..., example=60.0, description="Exact end second of the clip (Max 20s difference from start)")

class DownloadClipsRequest(BaseModel):
    clips: List[ClipRequest]

# ======= ENDPOINTS =======

@router.post("/search", summary="Search videos based on keyword and platform with filters")
def miner_search(req: MinerSearchRequest):
    """
    **Module 1: Miner - Step 1**
    Searches for viral videos on the selected platform using advanced filters.
    """
    if req.platform.lower() == "youtube":
        results = search_youtube_videos(
            query=req.query,
            max_results=req.max_results,
            filter_time=req.filter_time,
            channel_name=req.channel_name
        )
        return {"data": results}

    elif req.platform.lower() == "tiktok":
        results = mock_tiktok_search(query=req.query)
        return {"data": results}

    else:
        raise HTTPException(status_code=400, detail="Platform not supported. Use 'youtube' or 'tiktok'.")


@router.get("/highlights", summary="Fetch exact transcript timestamps for a keyword")
def miner_get_highlights(video_url: str = Query(...), query_word: str = Query(...)):
    """
    **Module 1: Miner - Step 2**
    Pulls the transcript of the video (currently YouTube only) and finds exact timestamps
    where the queried keyword is spoken. Useful for UI rendering.
    """
    if "youtube.com" in video_url or "youtu.be" in video_url:
        return get_youtube_highlights(video_url, query_word)
    else:
        raise HTTPException(status_code=501, detail="Automatic transcription currently supported for YouTube only.")


from fastapi.concurrency import run_in_threadpool
import asyncio
import uuid

@router.post("/download-clips", summary="Slice and package selected video fragments")
async def miner_download_clips(req: DownloadClipsRequest):
    """
    **Module 1: Miner - Step 3**
    Receives a list of selected clips with precise slider timestamps.
    The backend uses concurrent threaded streams to slice exactly that portion.
    Strictly enforced constraint: Maximum 20 seconds per clip.
    """
    downloaded_files = []
    
    # Pre-validate all clips before starting to avoid partial failures mid-job
    for idx, clip in enumerate(req.clips):
        if (clip.end_time - clip.start_time) > 20:
            raise HTTPException(status_code=400, detail=f"Clip {idx} exceeds the strict maximum limit of 20 seconds.")

    # Wrap the blocking yt-dlp call to be run in a threadpool so it doesn't block the async loop
    async def process_clip(idx, clip):
        output_name = f"clip_{idx}_{uuid.uuid4().hex[:8]}_miner"
        try:
            # yt-dlp is a synchronous blocking operation. run_in_threadpool enables concurrency in FastAPI
            path = await run_in_threadpool(download_video_clip, clip.video_url, clip.start_time, clip.end_time, output_name)
            return path
        except Exception as e:
            print(f"Error packaging clip {idx}: {e}")
            return None

    # Process all selected videos concurrently
    results = await asyncio.gather(*(process_clip(idx, clip) for idx, clip in enumerate(req.clips)))
    downloaded_files = [path for path in results if path is not None]

    if not downloaded_files:
        raise HTTPException(status_code=500, detail="No clips could be generated.")
        
    return {
        "message": f"Successfully generated {len(downloaded_files)} clips concurrently in 'tmp_downloads' folder.",
        "files": downloaded_files
    }
